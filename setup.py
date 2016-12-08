from setuptools import setup

if __name__ == '__main__':
    setup(
        name='encrypted-storage',
        version='1.0.2',
        author='Zach Kazanski',
        author_email='kazanski.zachary@gmail.com',
        description='Easy, cryptographically secure storage on numerous database backends.',
        url="https://github.com/Kazanz/encrypted_storage",
        download_url="https://github.com/kazanz/encrypted_storage/tarball/1.0.0",
        packages=['encrypted_storage'],
        keywords=['cryptography', 'encryption'],
        install_requires=[
            'futures==3.0.3',
            'pycrypto==2.6.1',
            'python-swiftclient==2.5.0',
            'redis==2.10.3',
            'requests==2.7.0',
            'six==1.9.0',
        ],
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
