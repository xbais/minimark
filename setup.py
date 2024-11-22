import os, traceback
from distutils.core import setup
from setuptools.command.install import install

'''
try: 
    print("### Installing NVM ###")
    os.system("curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash")

    print("\n\n### Installing Puppeteer ###")   
    os.system("npx puppeteer browsers install chrome-headless-shell")

    print("\n\n### Installing Mermaid CLI : mmdc ###")
    os.system("npm install -g @mermaid-js/mermaid-cli")
except Exception as e:
    print(traceback.format_exc())
'''

class PostInstallCommand(install):
    """Post-installation for installation mode."""
    def run(self):
        install.run(self)
        print("\nPlease add the following line to your shell configuration (e.g., .bashrc or .zshrc):")
        print("alias minimark='python3 -m minimark'")
        print("Once added, you can use 'minimark' command to run the app.")


try:
    import pypandoc
    long_description = pypandoc.convert_file('README.md', 'rst')
except (IOError, ImportError):
    long_description = open('README.md').read()


setup(name='minimark',
    version = '0.0.2.0',
    description='MiniMark : The CLI Markdown Editor / Viewer',
    long_description_content_type = 'text/markdown',
    long_description=long_description,
    author = 'Aakash Singh Bais',
    author_email='xbais@duck.com',
    url='https://github.com/xbais/minimark',
    package_dir = {'':'src'},
    packages=['minimark'],
    install_requires=[
        'numpy',    
        'argparse', 
        'textual',
        'textual_image',
        'matplotlib',
        'pillow',
        'cairosvg',
        'tqdm',
        'art',
        'tree-sitter==0.21.3',
        'tree-sitter-languages==1.10.2',
        'asyncio',
        'requests',
    ],
    license='GPLv3',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: POSIX :: Linux',

    ],
    python_requires='>=3.6',
    entry_points={
        'console_scripts': [
            'minimark=minimark.__main__:main',  # Point to the main function
        ],
    },
    cmdclass={
        'install': PostInstallCommand,
    },
    package_data={
        'minimark':['data/*'],
    },
)
