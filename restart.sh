touch /etc/uwsgi/apps/call.ini
supervisorctl restart agents-call-jobs
npm run build
