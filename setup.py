import os, traceback
from distutils.core import setup, find_packages

try: 
    print("### Installing NVM ###")
    os.system("curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash")

    print("\n\n### Installing Puppeteer ###")
    os.system("npx puppeteer browsers install chrome-headless-shell")

    print("\n\n### Installing Mermaid CLI : mmdc ###")
    os.system("npm install -g @mermaid-js/mermaid-cli")
except Exception as e:
    print(traceback.format_exc())

try:
    import pypandoc
    long_description = pypandoc.convert_file('README.md', 'rst')
except (IOError, ImportError):
    long_description = open('README.md').read()


setup(name='minimark',
    version = '0.0.1',
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
        'pillow',
        'cairosvg',
        'shutil',
        'tqdm',
        'art',
        'tree-sitter==0.21.3',
        'tree-sitter-languages==1.10.2',
        'asyncio',
        'traceback'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
