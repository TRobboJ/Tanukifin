import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('build', SCRIPTS / 'build.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class ApkInspection(unittest.TestCase):
    def inspect(self, permission='BLUETOOTH', native='libandroidx.graphics.path.so', package='org.tanukifin.tv'):
        with tempfile.TemporaryDirectory() as directory:
            apk = Path(directory) / 'test.apk'
            with zipfile.ZipFile(apk, 'w') as archive:
                # Inert text entry: not executable code and not an antivirus test sample.
                archive.writestr('lib/arm64-v8a/' + native, 'benign test metadata')
            xml = '<manifest xmlns:android="http://schemas.android.com/apk/res/android">' \
                  f'<uses-permission android:name="android.permission.{permission}" android:maxSdkVersion="30"/>' \
                  '</manifest>'
            with patch.object(build, 'android_tool', return_value='apkanalyzer'), \
                 patch.object(build.subprocess, 'check_output', side_effect=[package, xml]):
                return build.inspect_apk(apk)

    def test_permission_max_sdk_is_not_part_of_permission_name(self):
        self.assertEqual(self.inspect()['permissions'], ['android.permission.BLUETOOTH'])

    def test_unexpected_permission_is_rejected(self):
        with self.assertRaises(ValueError):
            self.inspect(permission='CAMERA')

    def test_unexpected_native_code_is_rejected(self):
        with self.assertRaises(ValueError):
            self.inspect(native='libunexpected.so')

    def test_wrong_package_is_rejected(self):
        with self.assertRaises(ValueError):
            self.inspect(package='org.example.other')


if __name__ == '__main__':
    unittest.main()
