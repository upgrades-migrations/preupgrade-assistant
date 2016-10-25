# -*- coding: utf-8 -*-
import uuid
from django.core.urlresolvers import reverse
import os

from preupg.ui.report.models import Run, Host
from preupg.ui.report.service import import_report

from django.conf import settings


__all__ = (
    'upload_results',
    'submit_new',
    "ping",
)

def ping(request):
    """ server verification """
    return {'status': "OK"}

def upload_results(request, opts):
    """
    upload_results(opts)

    opts is dictionary, it has to contain these entries:
     * filename: tarball's filename
     * data: content of file
     * runhost_id: ID of run for specific host
    """
    p = os.path.join(settings.MEDIA_ROOT, opts['filename'])
    with open(p, 'wb+') as destination:
        destination.write(opts['data'].data)
    import_report(p, opts['hostrun_id'])
    return 'OK'

def submit_new(request, opts):
    """
    submit_new(opts)

    submit a new result of a run on (probably remote) host

    opts is dictionary, it has to contain these entries:
     * host: string with hostname of a host where scan was done (optional)
     * data: content of file
    """
    # as soon as the tarball will be unpacked, this die will be erased
    tmp_dir = os.path.join(settings.MEDIA_ROOT, uuid.uuid4().hex)
    try:
        os.makedirs(tmp_dir, mode=0o0744)
    except OSError as e:
        # TODO: log
        return {
            'status': 'ERROR',
            'message': 'Failed to create temporary directory: %s' % e,
        }
    report_path = os.path.join(tmp_dir, 'result.tar.gz')
    with open(report_path, 'wb+') as destination:
        destination.write(opts['data'].data)

    host, created = Host.objects.get_or_create(hostname=opts['host'])
    run_object = Run.objects.create_for_host(host)
    hostrun = run_object.first_hostrun()

    import_report(report_path, hostrun.id)
    rel_url = reverse('result-detail', args=(hostrun.result.id, ))
    return {'status': 'OK', 'url': request.build_absolute_uri(rel_url)}
