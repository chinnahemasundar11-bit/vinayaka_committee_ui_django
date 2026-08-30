import os
import sys
import time
import pytest

sys.path.insert(0, os.path.abspath("."))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
try:
    django.setup()
except Exception:
    pass


class PytestPostgresCollector:
    def __init__(self):
        self.start_time = time.time()
        self.results = []
        self.branch = os.environ.get("GIT_BRANCH", "release/2.4")
        self.commit_hash = os.environ.get("GIT_COMMIT", "a82f91c")
        self.app_version = "v2.4"

    def determine_severity(self, module, test_name, error):
        error_str = str(error).lower()
        if "critical" in test_name or "auth" in module or "permission" in error_str or "database" in error_str:
            return "CRITICAL"
        elif "high" in test_name or "workflow" in module or "payment" in error_str:
            return "HIGH"
        elif "medium" in test_name or "validation" in error_str or "form" in error_str:
            return "MEDIUM"
        return "LOW"

    def record_result(self, item, call, report):
        if report.when != "call" and not (report.when == "setup" and report.failed):
            return

        # Extract module name from file path
        path_parts = item.fspath.strpath.replace("\\", "/").split("/")
        filename = path_parts[-1]
        module = filename.replace("test_", "").replace(".py", "")

        status = "PASSED"
        if report.failed:
            status = "FAILED"
        elif report.skipped:
            status = "SKIPPED"

        error_msg = str(report.longrepr) if report.failed else None
        duration_ms = report.duration * 1000
        severity = self.determine_severity(module, item.name, error_msg)

        self.results.append({
            "module": module,
            "test_name": item.name,
            "status": status,
            "error": error_msg,
            "severity": severity,
            "duration_ms": duration_ms
        })

    def finalize_run(self):
        from django.utils import timezone
        from qa_dashboard.models import TestRun, TestResult, TestIssue

        total = len(self.results)
        if total == 0:
            return None

        passed = sum(1 for r in self.results if r["status"] == "PASSED")
        failed = sum(1 for r in self.results if r["status"] == "FAILED")
        skipped = sum(1 for r in self.results if r["status"] == "SKIPPED")
        pass_rate = (passed / total) * 100.0 if total > 0 else 0.0
        duration_sec = time.time() - self.start_time

        run = TestRun.objects.create(
            timestamp=timezone.now(),
            branch=self.branch,
            commit_hash=self.commit_hash,
            application_version=self.app_version,
            total_tests=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            pass_rate=pass_rate,
            duration_seconds=duration_sec
        )

        for res in self.results:
            TestResult.objects.create(
                run=run,
                module=res["module"],
                test_name=res["test_name"],
                test_status=res["status"],
                error_message=res["error"],
                severity=res["severity"],
                duration_ms=res["duration_ms"]
            )

            # Process failure tracking issues
            if res["status"] == "FAILED":
                issue, created = TestIssue.objects.get_or_create(
                    module=res["module"],
                    test_name=res["test_name"],
                    defaults={
                        "severity": res["severity"],
                        "status": "OPEN",
                        "failure_count": 1,
                        "first_seen": timezone.now(),
                        "last_seen": timezone.now(),
                        "latest_error": res["error"],
                        "branch": self.branch,
                        "commit_hash": self.commit_hash
                    }
                )
                if not created:
                    issue.failure_count += 1
                    issue.last_seen = timezone.now()
                    issue.latest_error = res["error"]
                    issue.status = "OPEN"
                    issue.save()
            elif res["status"] == "PASSED":
                # Auto-resolve existing open issues
                TestIssue.objects.filter(module=res["module"], test_name=res["test_name"]).update(status="RESOLVED")

        return run

collector_instance = PytestPostgresCollector()

def pytest_runtest_logreport(report):
    if hasattr(report, "item"):
        collector_instance.record_result(report.item, None, report)

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    report.item = item

def pytest_sessionfinish(session, exitstatus):
    collector_instance.finalize_run()
