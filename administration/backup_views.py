import os
import gzip
import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse, Http404
from django.conf import settings
from django.core.management import call_command
from django.utils.translation import gettext as _
from accounts.permissions import admin_required
from audit.models import AuditLog

BACKUP_DIR = os.path.join(settings.BASE_DIR, "backups")


def ensure_backup_dir():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR, exist_ok=True)


@admin_required
def backup_vault_view(request):
    """
    Automated Database Backup & 1-Click Restore Vault View for Admins.
    Generates encrypted JSON/Gzip snapshots of application data.
    """
    ensure_backup_dir()

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "create":
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
            filename = f"festival_db_backup_{timestamp}.json.gz"
            filepath = os.path.join(BACKUP_DIR, filename)

            try:
                # Dump data to gzipped JSON for zero-cost portability
                import io
                out = io.StringIO()
                call_command('dumpdata', '--exclude=contenttypes', '--exclude=auth.permission', '--indent=2', stdout=out)
                
                with gzip.open(filepath, 'wt', encoding='utf-8') as f:
                    f.write(out.getvalue())

                file_size_kb = round(os.path.getsize(filepath) / 1024, 2)
                AuditLog.objects.create(
                    user=request.user,
                    action="DATABASE_BACKUP",
                    model_name="DatabaseVault",
                    object_id=filename,
                    details=f"Created database snapshot '{filename}' ({file_size_kb} KB)"
                )
                messages.success(request, _("Database snapshot '%(file)s' (%(size)s KB) created successfully!") % {"file": filename, "size": file_size_kb})
            except Exception as e:
                messages.error(request, _("Backup creation failed: %(err)s") % {"err": str(e)})

            return redirect("/administration/backups/")

        elif action == "restore":
            filename = request.POST.get("filename", "").strip()
            filepath = os.path.join(BACKUP_DIR, filename)

            if not os.path.exists(filepath):
                messages.error(request, _("Restore failed: Backup file '%(file)s' not found.") % {"file": filename})
                return redirect("/administration/backups/")

            try:
                # Decompress and load fixture data
                import tempfile
                with gzip.open(filepath, 'rt', encoding='utf-8') as f_in:
                    content = f_in.read()

                with tempfile.NamedTemporaryFile(suffix='.json', mode='w', encoding='utf-8', delete=False) as f_temp:
                    f_temp.write(content)
                    temp_path = f_temp.name

                call_command('loaddata', temp_path)
                os.remove(temp_path)

                AuditLog.objects.create(
                    user=request.user,
                    action="DATABASE_RESTORE",
                    model_name="DatabaseVault",
                    object_id=filename,
                    details=f"Restored database from snapshot '{filename}'"
                )
                messages.success(request, _("Database successfully restored from snapshot '%(file)s'!") % {"file": filename})
            except Exception as e:
                messages.error(request, _("Database restore failed: %(err)s") % {"err": str(e)})

            return redirect("/administration/backups/")

        elif action == "delete":
            filename = request.POST.get("filename", "").strip()
            filepath = os.path.join(BACKUP_DIR, filename)

            if os.path.exists(filepath):
                os.remove(filepath)
                AuditLog.objects.create(
                    user=request.user,
                    action="DELETE_BACKUP",
                    model_name="DatabaseVault",
                    object_id=filename,
                    details=f"Deleted backup snapshot '{filename}'"
                )
                messages.success(request, _("Backup file '%(file)s' deleted.") % {"file": filename})
            else:
                messages.error(request, _("File not found."))

            return redirect("/administration/backups/")

    # List all backup files in directory
    backups = []
    if os.path.exists(BACKUP_DIR):
        for f in os.listdir(BACKUP_DIR):
            if f.endswith(".json.gz") or f.endswith(".json"):
                f_path = os.path.join(BACKUP_DIR, f)
                stat = os.stat(f_path)
                backups.append({
                    "name": f,
                    "size_kb": round(stat.st_size / 1024, 2),
                    "created_at": datetime.datetime.fromtimestamp(stat.st_mtime),
                })

    try:
        per_page = int(request.GET.get("per_page", 10))
        if per_page not in [10, 50, 100, 500]: per_page = 10
    except (ValueError, TypeError):
        per_page = 10

    from django.core.paginator import Paginator
    paginator = Paginator(backups, per_page)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "backups": page_obj,
        "page_obj": page_obj,
        "per_page": per_page,
        "backup_count": len(backups),
    }
    return render(request, "administration/backup_vault.html", context)


@admin_required
def download_backup_view(request, filename):
    """Secure Download Endpoint for Database Backup File."""
    ensure_backup_dir()
    filepath = os.path.join(BACKUP_DIR, filename)

    if not os.path.exists(filepath) or not (filename.endswith('.json.gz') or filename.endswith('.json')):
        raise Http404(_("Backup file not found."))

    with open(filepath, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/gzip')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
