import os
from setuptools import setup


def build_install_requires(path):
    basedir = os.path.dirname(path)
    with open(path) as f:
        reqs = []
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line[0] == '#':
                continue
            elif line.startswith('-r '):
                nested_req = line[3:].strip()
                nested_path = os.path.join(basedir, nested_req)
                reqs += build_install_requires(nested_path)
            elif line[0] == '-':
                continue
            else:
                reqs.append(line)
        return reqs


reqs = build_install_requires('reqs/base.txt')


if __name__ == '__main__':
    setup(
        name='encrypted-storage',
        version='1.0.0',
        author='Zach Kazanski',
        author_email='kazanski.zachary@gmail.com',
        description='Easy, crytographically secure storage on numerous database backends.',
        url="https://github.com/Kazanz/encrypted_storage",
        download_url="https://github.com/kazanz/encrypted_storage/tarball/1.0.0",
        packages=['encrypted_storage'],
        install_requires=reqs,
        keywords=['cryptography', 'encryption'],
        classifiers=[
            'Programming Language :: Python',
            'Development Status :: 5 - Production/Stable',
            'Intended Audience :: Developers',
            'Operating System :: OS Independent',
            'License :: OSI Approved :: MIT License',
            'Programming Language :: Python :: 2.7',
            'Topic :: Security :: Cryptography',
        ],
    )
