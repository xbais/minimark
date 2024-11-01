# MiniMark : The CLI Markdown Editor / Viewer
![image](https://github.com/user-attachments/assets/7dd69419-4c7b-41db-a1fd-5439c8a5a222)
## Installation Pre-requisites
1. Install NVM Package Manager : `curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash`
2. Install Pupetteer : `npx puppeteer browsers install chrome-headless-shell`
3. Install Mermaid CLI : `npm install -g @mermaid-js/mermaid-cli`
4. Install Ripgrep Utility : `sudo apt install ripgrep`

## Installation & Usage
1. Install MiniMark : (in Ubuntu < 24.04 LTS) `pip3 install minimark`, (in Ubuntu 24.04 LTS) `pip3 install minimark --break-system-packages` (NOTE : Ubuntu 24 does not allow installing any python packages without the additional flag, but rest assured : IT IS SAFE, if you dont want this, you can install Minimark in a separate Python venv)
2. Create Alias for MiniMark : add the following line at the end of your `~/.bashrc` file (if you use Bash), or your `~/.zshrc` file (if you use ZSH) : `alias minimark='python3 -m minimark'`
Now, you can run MiniMark using the terminal command : `minimark` !! Enjoy!

NOTE:
- If you dont want to create an alias, you can still run MiniMark using the command : `python3 -m minimark`
