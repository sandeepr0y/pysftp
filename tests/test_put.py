'''test pysftp.Connection.put - uses py.test'''

# pylint: disable = W0142
# pylint: disable=E1101
from common import *
from mock import Mock
from time import sleep


def test_put_callback(sftpserver):
    '''test the callback feature of put'''
    with sftpserver.serve_content(CONTENT):
        with pysftp.Connection(**conn(sftpserver)) as psftp:
            cback = Mock(return_value=None)
            with tempfile_containing(contents=8192*'*') as fname:
                base_fname = os.path.split(fname)[1]
                psftp.chdir('/pub/foo2/bar1')
                psftp.put(fname, callback=cback)
                # clean up
                psftp.remove(base_fname)
            # verify callback was called more than once - usually a min of 2
            assert cback.call_count >= 2


def test_put_confirm(sftpserver):
    '''test the confirm feature of put'''
    with sftpserver.serve_content(CONTENT):
        with pysftp.Connection(**conn(sftpserver)) as psftp:
            with tempfile_containing(contents=8192*'*') as fname:
                base_fname = os.path.split(fname)[1]
                psftp.chdir('/pub/foo2/bar1')
                result = psftp.put(fname)
                # clean up
                psftp.remove(base_fname)
            # verify that an SFTPAttribute like os.stat was returned
            assert result.st_size == 8192
            assert result.st_uid is not None
            assert result.st_gid is not None
            assert result.st_atime
            assert result.st_mtime


@skip_if_ci
def test_put(sftpserver):
    '''run test on localhost'''
    with sftpserver.serve_content(CONTENT):
        with pysftp.Connection(**conn(sftpserver)) as psftp:
            contents = 'now is the time\nfor all good...'
            with tempfile_containing(contents=contents) as fname:
                base_fname = os.path.split(fname)[1]
                if base_fname in psftp.listdir():
                    psftp.remove(base_fname)
                assert base_fname not in psftp.listdir()
                psftp.put(fname)
                assert base_fname in psftp.listdir()
                with tempfile_containing('') as tfile:
                    psftp.get(base_fname, tfile)
                    assert open(tfile).read() == contents
                # clean up
                psftp.remove(base_fname)


def test_put_bad_local(sftpserver):
    '''try to put a non-existing file to a read-only server'''
    with sftpserver.serve_content(CONTENT):
        with pysftp.Connection(**conn(sftpserver)) as psftp:
            with tempfile_containing('should fail') as fname:
                pass
            # tempfile has been removed
            with pytest.raises(OSError):
                psftp.put(fname)


# TODO
# def test_put_not_allowed(psftp):
#     '''try to put a file to a read-only server'''
#     with tempfile_containing('should fail') as fname:
#         with pytest.raises(IOError):
#             psftp.put(fname)


@skip_if_ci
def test_put_preserve_mtime(lsftp):
    '''test that m_time is preserved from local to remote, when put'''
    with tempfile_containing(contents=8192*'*') as fname:
        base_fname = os.path.split(fname)[1]
        base = os.stat(fname)
        # with pysftp.Connection(**SFTP_LOCAL) as sftp:
        result1 = lsftp.put(fname, preserve_mtime=True)
        sleep(2)
        result2 = lsftp.put(fname, preserve_mtime=True)
        # clean up
        lsftp.remove(base_fname)
    # see if times are modified
    # assert base.st_atime == result1.st_atime
    assert int(base.st_mtime) == result1.st_mtime
    # assert result1.st_atime == result2.st_atime
    assert int(result1.st_mtime) == result2.st_mtime
