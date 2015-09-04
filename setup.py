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
        description='Asymetrically encrypt/decrypt symetrically encrypted/decrypted data on numerous backends.',
        long_description=open('README.md').read(),
        packages=['encrypted_storage'],
        install_requires=reqs,
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
