from PyInstaller.utils.hooks import copy_metadata

datas = copy_metadata('z3c.rml')

# This really doesn't belong here, but is better than hacking PyInstaller's "hook-google.api_core.py" which
# is missing this. Without it, we get a "pkg_resources.DistributionNotFound" runtime error saying:
#    The 'google-api-python-client' distribution was not found and is required by the application
datas += copy_metadata('google-api-python-client')
