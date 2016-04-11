
try:
	from subprocess import CalledProcessError, check_call
	from os import devnull
	FNULL = open(devnull, 'r+b')
	trash1 = check_call(['which', 'which'], stdin=FNULL, stdout=FNULL, stderr=FNULL)
	trash2 = check_call(['which', 'highlight'], stdin=FNULL, stdout=FNULL, stderr=FNULL)
except CalledProcessError as e:
	print('Command \'{}\' was unable to run, return code {}'.format(e.cmd, e.returncode))

