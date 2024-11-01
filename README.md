# MiniMark : The CLI Markdown Editor / Viewer
![OS](https://img.shields.io/badge/OS-Linux-green) ![Python Version](https://img.shields.io/pypi/pyversions/minimark) ![License](https://img.shields.io/github/license/xbais/minimark) ![version](https://img.shields.io/pypi/v/minimark)

<p align="center">
  <img src="./_resources/logo.jpeg" alt="Sublime's custom image" style='width:300px'/>
</p>

![image](https://github.com/user-attachments/assets/7dd69419-4c7b-41db-a1fd-5439c8a5a222)
## 🔷 Installation of Pre-requisites
1. Install [NVM Package Manager](https://github.com/nvm-sh/nvm) : 
  ```bash
  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
  ```
2. Install [Pupetteer](https://pptr.dev) : 
  ```bash
  npx puppeteer browsers install chrome-headless-shell
  ```
3. Install [Mermaid CLI](https://github.com/mermaid-js/mermaid-cli) : 
  ```bash
  npm install -g @mermaid-js/mermaid-cli
  ```
4. Install [Ripgrep](https://github.com/BurntSushi/ripgrep) Utility :
  ```bash
  sudo apt install ripgrep
  ```

## 🔷 Installation & Usage
1. Install MiniMark : (in Ubuntu < 24.04 LTS) `pip3 install minimark`, (in Ubuntu 24.04 LTS) `pip3 install minimark --break-system-packages` (NOTE : Ubuntu 24 does not allow installing any python packages without the additional flag, but rest assured : IT IS SAFE, if you dont want this, you can install Minimark in a separate Python venv)
2. Create Alias for MiniMark : add the following line at the end of your `~/.bashrc` file (if you use Bash), or your `~/.zshrc` file (if you use ZSH) : `alias minimark='python3 -m minimark'`
Now, you can run MiniMark using the terminal command : `minimark` !! Enjoy!

NOTE:
- If you dont want to create an alias, you can still run MiniMark using the command : `python3 -m minimark`
