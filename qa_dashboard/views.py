import subprocess
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Count, Q
from django.views.decorators.csrf import csrf_exempt
from accounts.permissions import admin_required
from .models import TestRun, TestResult, TestIssue


@admin_required
def index(request):
    """QA Automation & Test Dashboard Main View."""
    latest_run = TestRun.objects.first()
    open_issues = TestIssue.objects.filter(status="OPEN")

    critical_count = open_issues.filter(severity="CRITICAL").count()
    high_count = open_issues.filter(severity="HIGH").count()
    medium_count = open_issues.filter(severity="MEDIUM").count()
    low_count = open_issues.filter(severity="LOW").count()

    failing_modules = open_issues.values("module").annotate(fail_count=Count("id")).order_by("-fail_count")

    recent_runs = TestRun.objects.all()[:10]

    context = {
        "latest_run": latest_run,
        "open_issues": open_issues,
        "critical_count": critical_count,
        "high_count": high_count,
        "medium_count": medium_count,
        "low_count": low_count,
        "failing_modules": failing_modules,
        "recent_runs": recent_runs,
    }
    return render(request, "qa_dashboard/test_dashboard.html", context)


@admin_required
def api_metrics(request):
    """REST API endpoint returning current QA test health metrics JSON."""
    latest_run = TestRun.objects.first()
    open_issues = TestIssue.objects.filter(status="OPEN")

    data = {
        "latest_run": {
            "id": latest_run.id if latest_run else None,
            "total_tests": latest_run.total_tests if latest_run else 0,
            "passed": latest_run.passed if latest_run else 0,
            "failed": latest_run.failed if latest_run else 0,
            "skipped": latest_run.skipped if latest_run else 0,
            "pass_rate": latest_run.pass_rate if latest_run else 0.0,
            "branch": latest_run.branch if latest_run else "main",
            "commit_hash": latest_run.commit_hash if latest_run else "a82f91c",
            "timestamp": latest_run.timestamp.isoformat() if latest_run else None
        },
        "issues_by_severity": {
            "CRITICAL": open_issues.filter(severity="CRITICAL").count(),
            "HIGH": open_issues.filter(severity="HIGH").count(),
            "MEDIUM": open_issues.filter(severity="MEDIUM").count(),
            "LOW": open_issues.filter(severity="LOW").count()
        },
        "failing_modules": list(open_issues.values("module").annotate(fail_count=Count("id")).order_by("-fail_count"))
    }
    return JsonResponse(data)


@admin_required
@csrf_exempt
def api_run_tests(request):
    """REST API endpoint triggering full Pytest automated test execution."""
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST method required"}, status=405)

    try:
        cmd = ["pytest", "testcases/", "-p", "qa_dashboard.pytest_plugin"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        latest_run = TestRun.objects.first()
        return JsonResponse({
            "status": "success",
            "returncode": result.returncode,
            "pass_rate": latest_run.pass_rate if latest_run else 0.0,
            "total_tests": latest_run.total_tests if latest_run else 0,
            "failed": latest_run.failed if latest_run else 0
        })
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
