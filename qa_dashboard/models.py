from django.db import models
from django.utils import timezone


class TestRun(models.Model):
    """Stores full test suite execution run metadata."""
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    branch = models.CharField(max_length=100, default="main")
    commit_hash = models.CharField(max_length=40, default="a82f91c")
    application_version = models.CharField(max_length=50, default="v2.4")
    total_tests = models.IntegerField(default=0)
    passed = models.IntegerField(default=0)
    failed = models.IntegerField(default=0)
    skipped = models.IntegerField(default=0)
    pass_rate = models.FloatField(default=0.0)
    duration_seconds = models.FloatField(default=0.0)

    class Meta:
        db_table = "qa_test_run"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"Run #{self.id} | Pass Rate: {self.pass_rate:.1f}% ({self.timestamp.strftime('%Y-%m-%d %H:%M')})"


class TestResult(models.Model):
    """Stores individual test execution outcome in a run."""
    run = models.ForeignKey(TestRun, on_delete=models.CASCADE, related_name="results")
    module = models.CharField(max_length=100, db_index=True)
    test_name = models.CharField(max_length=255)
    test_status = models.CharField(max_length=20, default="PASSED") # PASSED, FAILED, SKIPPED
    error_message = models.TextField(blank=True, null=True)
    severity = models.CharField(max_length=20, default="MEDIUM") # CRITICAL, HIGH, MEDIUM, LOW
    duration_ms = models.FloatField(default=0.0)

    class Meta:
        db_table = "qa_test_result"
        ordering = ["module", "test_name"]

    def __str__(self):
        return f"{self.module}::{self.test_name} - {self.test_status}"


class TestIssue(models.Model):
    """Tracks persistent test failure history across multiple runs."""
    module = models.CharField(max_length=100, db_index=True)
    test_name = models.CharField(max_length=255, unique=True)
    severity = models.CharField(max_length=20, default="HIGH") # CRITICAL, HIGH, MEDIUM, LOW
    status = models.CharField(max_length=20, default="OPEN") # OPEN, RESOLVED, IGNORED
    failure_count = models.IntegerField(default=1)
    first_seen = models.DateTimeField(default=timezone.now)
    last_seen = models.DateTimeField(default=timezone.now)
    latest_error = models.TextField(blank=True, null=True)
    branch = models.CharField(max_length=100, default="main")
    commit_hash = models.CharField(max_length=40, default="a82f91c")

    class Meta:
        db_table = "qa_test_issue"
        ordering = ["-severity", "-last_seen"]

    def __str__(self):
        return f"[{self.severity}] {self.module}::{self.test_name} (Failures: {self.failure_count})"
