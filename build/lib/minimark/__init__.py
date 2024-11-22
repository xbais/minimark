###########################
#        MINIMARK         #
# (By Aakash Singh Bais)  #
###########################

import numpy as np 
#import textual
import argparse
from textual import on
from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer, Container, Vertical, Horizontal, Grid
from textual.validation import Function, Number, ValidationResult, Validator
from textual.widgets import LoadingIndicator, Tree, Button, Footer, Header, Static, Label, ListItem, ListView, TextArea, DataTable, Rule, Markdown, DirectoryTree, Input, Pretty, TabbedContent, TabPane
from PIL import Image as PILImage # pillow==latest
import io, base64, subprocess, os, hashlib, shutil, traceback, getpass
import requests
import cairosvg
import shutil
from time import sleep
from tqdm import tqdm
from textual.app import App, ComposeResult
from textual_image.widget import Image
from textual.screen import Screen
import textual_image.renderable
from art import text2art
# https://github.com/lnqs/textual-image

import tree_sitter # tree-sitter==0.21.3
from tree_sitter_languages import get_language # tree-sitter-languages==1.10.2
# Specific versions required (error prevention) : https://github.com/grantjenks/py-tree-sitter-languages/issues/64
from rich import console
from pathlib import Path
import matplotlib.pyplot as plt

from textual.app import App, ComposeResult
from textual.color import Gradient
from textual.containers import Center, Middle
from textual.widgets import ProgressBar
import asyncio
import traceback
from pathlib import Path


#### GLOBALS ####
CWD, PARENT_PATH, app_logger, app, print, TOC_TREE, node_counter, width_factor, VIEW_MODE_SCREEN, HELP_SCREEN, EDIT_SCREEN, SEARCH_SCREEN, search_results, _trash_dir, md_file, CACHE_DIR = [None]*16
CURRENT_ROW_MD_CONTENT_WIDTH, CURRENT_ROW_WORD_LIST = 0, []
APP_SIZE = [0,0]
HISTORY = []
#################

class history():
    '''
    This class keeps track of the history of files being opened
    '''
    def __init__(self):
        self.data = [] # will store the history
        self.position = 0 # will keep track of the position of current doc in history

    def add(self, path:str):
        # Add a new path to the history
        if self.position == 0:
            self.data.append(path)
        elif self.position < 0:
            self.data = self.data[:-self.position]
            self.position = 0
            self.data.append(path)
    
    def previous(self):
        # Go to previous position
        if self.position == - len(self.data)+1:
            app_logger.log('This is the first file in history.')
        else:
            self.position -= 1
    
    def next(self):
        # Go to next position
        if self.position == 0:
            app_logger.log('This is the last file in history.')
        else:
            self.position += 1

    def get_path(self):
        # Get the path of the current directory
        global app_logger
        app_logger.log(f'position = {self.position}, data = {self.data}')
        return self.data[self.position-1]


def get_cwd() -> str:
    # Get the directory of the currently executing script
    return str(Path(__file__).resolve().parent)

def create_dir(dir:str, overwrite:bool=False) -> str:
    if os.path.exists(dir):
        if overwrite:
            # Remove the directory and its contents recursively
            pass
        else:
            return dir
    # Create directory
    os.makedirs(dir)
    return dir

def async_wrapper(func):
    """
    A decorator to make any synchronous function asynchronous.
    """

    async def wrapper(*args, **kwargs):
        # Run the function in a separate thread
        return await asyncio.to_thread(func, *args, **kwargs)

    return wrapper
    
def safe_decode(byte_data):
    """Safely decode bytes to a string, using 'utf-8' with error handling."""
    try:
        return byte_data.decode('utf-8')
    except UnicodeDecodeError:
        # If an error occurs, decode using 'latin-1' as fallback or ignore errors.
        return byte_data.decode('latin-1', errors='ignore')
    
class NodeCounter():
    def __init__(self):
        self.counter = {}
    
    def plus(self, node_name:str):
        if node_name not in self.counter.keys():
            self.counter[node_name] = 1
        else:
            self.counter[node_name] += 1
        return self.get_count(node_name=node_name)

    def minus(self, node_name:str):
        if node_name not in self.counter.keys():
            self.counter[node_name] = 0
        else:
            self.counter[node_name] -= 1
        return self.get_count(node_name=node_name)

    def get_count(self, node_name:str):
        return self.counter[node_name]

    def get_counter(self):
        return self.counter
    
    def refresh(self):
        self.counter = {}

class TOC(): # Class to manage and keep track of the Table of contents
    def __init__(self,):
        self.refresh()

    def find_node(self, nodes, name):
        # Look for a node with the specified name within the given nodes
        app_logger.log('Iterable length : ', len(nodes))
        for node in nodes:
            app_logger.log(name, ' <--> ', node.label)
            if node.label == name:
                return node
            else:
                app_logger.log(name, ' not equal to ', node.label)

            # Check in children
            child_nodes = self.tree.children(node)
            for child in child_nodes:
                found_node = self.find_node([child], name)
                if found_node:
                    return found_node

        return None  # Return None if the node was not found

    def get_parent(self, expected_parent_numeral:str):
        expected_parent_numeral = expected_parent_numeral.split('.')
        for id in range(len(expected_parent_numeral)):
            test_numeral = '.'.join(expected_parent_numeral[:-id]) if id != 0 else '.'.join(expected_parent_numeral)
            if test_numeral in self.tree_meta.keys():
                return self.tree_meta[test_numeral][1]
        return self.tree.root

    def add_heading(self, heading:str, label_id:str, screen:Screen):
        heading_numeral = heading.split(' ')[0]
        heading_name = ' '.join(heading.split(' '))[1:]
        self.tree_meta[heading_numeral] = [heading, None, label_id]
        if heading_numeral == '0' and '0' not in self.tree_meta.keys():
            self.tree.root.label = heading_name
            self.tree.root.data = label_id
            self.tree_meta[heading_numeral] = [heading, self.tree.root, label_id]
            return
        # Get the parent, add the child to the parent in the tree 
        elif len(heading_numeral.split('.')) == 1:
            # Add to root
            _ = self.tree.root.add(heading, expand=True, data=label_id)
            self.tree_meta[heading_numeral] = [heading, _]
            app_logger.log(_) # (self.tree.walk_children(self.tree.root))
            #self.tree_meta[heading_numeral] = heading_name
        else:
            # Find parent, add to parent
            parent_numeral = '.'.join(heading_numeral.split('.')[:-1])
            parent_node = self.get_parent(expected_parent_numeral=parent_numeral)
            '''
            app_logger.log('Parent details (parent_numeral, name) : ', parent_numeral, self.tree_meta[parent_numeral])
            if parent_numeral in self.tree_meta.keys():
                # Get parent
                #parent = self.find_node(self.tree.children(self.tree.root), self.tree_meta[parent_numeral])
                #app_logger.log('Self.tree.children = ', self.tree.children)
                parent_node = self.tree_meta[parent_numeral][1] #self.find_node(self.tree.walk_children(self.tree.root), self.tree_meta[parent_numeral])
            '''
            if parent_node == None:
                app_logger.log('Parent is none. Heading = ', heading)
                app_logger.log(self.tree_meta)
            _ = parent_node.add(label=heading, expand=True, data=label_id)
            self.tree_meta[heading_numeral] = [heading, _]

    def get_tree(self):
        return self.tree
    
    def refresh(self):
        self.tree: Tree[dict] = Tree("This Document")
        self.tree.root.expand()
        self.tree_meta = {'0':['This Document', self.tree.root]} # numeral : heading_name

class logger():
    def __init__(self):
        # Create an empty log file, if already exists, delete it
        if os.path.isfile('.logs'):
            os.remove('.logs')
        
        #self.log_file = open('.logs', 'w')
    
    def log(self, *args)-> None:
        log_string = ''.join([str(_arg) for _arg in args]) 
        with open('.logs', 'a+') as log_file:    
            log_file.writelines([log_string + '\n' + '-'*5 + '\n',])
    
    async def async_log(self, *args)-> None:
        log_string = ''.join([str(_arg) for _arg in args]) 
        with open('.logs', 'a+') as log_file:    
            log_file.writelines([log_string + '\n' + '-'*5 + '\n',])

from textual.widgets import Label
from textual.reactive import Reactive

class BlockProgressBar(Label):
    def __init__(self, max_size: int = 5, id=None):
        super().__init__()
        self.current_state: Reactive[float] = Reactive(0)  # Track current percent
        self.max_size = max_size
        self.add_class('block_progress_bar')
        self.id = id
        self.text = 'Ready'

    def clear(self):
        self.text = ''

    async def update(self, percent: float):
        # Ensure percent is within valid range
        if 0 <= percent < 100:
            self.current_state = percent
            # Update text based on new percentage
            self.text = '#' * int(percent * self.max_size / 100)
            #await self.refresh()  # Refresh UI to show changes

def get_image_dims(path:str):
    """This fn simply returns image dims"""
    im = PILImage.open(path)
    width, height = im.size
    return width, height

def get_image_container(image_path:str, image_type:str, max_height:int, width_factor:float):
    """This fn returns the image container along with the image element"""
    img_type_to_description = {'img':'Fig.', 'cb-mermaid':'Diagram', 'latex':'Eqn.'}
    im = Image(image_path)
    im_format = image_path.split('.')[-1]
    width, height = get_image_dims(image_path)
    width, height = width*(max_height/height)*width_factor, max_height
    im.styles.width, im.styles.height = f'{width}', f'{height}'
    im.styles.width='auto' # experimental
    
    im.add_class('img')
    im.border_title = f'{img_type_to_description[image_type]} {node_counter.plus(image_type)}'
    im.border_subtitle = f'[{im_format.upper()}]'
    im.styles.align_horizontal = 'center'
    im.styles.align_vertical = 'middle'

    im_container = ScrollableContainer(im)
    im_container.classes = 'img_container'
    im_container.styles.height = height
    return im_container

def quick_hash(algo:str='sha256', string:str=''):
    """This fn returns the hash of a string"""
    h = hashlib.new(f'{algo}') # sha256 can be replaced with diffrent algorithms
    h.update(string.encode()) # give a encoded string. Makes the String to the Hash
    return str(h.hexdigest())

def mermaid_to_png(mermaid_code:str, output_path:str):
    """This takes mermaid diagram code and renders it to an image"""
    global app
    # Save the mermaid code into a .mmd file
    mermaid_file = output_path.replace('.png', '.mmd')
    with open(mermaid_file, 'w') as f:
        f.write(mermaid_code)
    
    # Use mermaid.cli to render the diagram
    try:
        _command = ['mmdc', '-i', mermaid_file, '-o', output_path, f"--puppeteerConfigFile {os.path.join(CWD, 'data', 'puppeteer-config.json')}"]
        app_logger.log(f'Using command : {" ".join(_command)}')
        os.system(' '.join(_command))
    except subprocess.CalledProcessError as e:
        app_logger.log(f"Error rendering Mermaid diagram: {e}")
        app.notify(f'{e} \n Mermaid diagram rendering requires MMDC. If not installed, install it : npx puppeteer browsers install chrome-headless-shell && sudo npm install -g @mermaid-js/mermaid-cli. If there are any issues remove these 2 packages and reinstall.', title='MMDC Not Found', timeout=20, severity='error')
    
    # Optionally remove the intermediate .mmd file
    #os.remove(mermaid_file)

def latex_to_png(latex_code, output_path, is_block: bool = False):
    """This fn takes Latex code and renders the equation to an image"""
    # Create a temporary figure and axis to calculate text size
    fig, ax = plt.subplots()
    
    # Render LaTeX code as text in display mode for block or inline
    if is_block:
        latex_code = r'$\displaystyle{}$'.format(latex_code)
    else:
        latex_code = r'${}$'.format(latex_code)
    
    # Add text to the axis and get bounding box
    text = ax.text(0.5, 0.5, latex_code, fontsize=10, ha='center', va='center')
    ax.axis('off')  # Hide axes
    
    # Draw figure to compute the size of the text
    fig.canvas.draw()
    bbox = text.get_window_extent(renderer=fig.canvas.get_renderer())
    
    # Calculate new figure size based on bounding box size
    width, height = bbox.width / fig.dpi, bbox.height / fig.dpi
    
    # Close the initial figure
    plt.close(fig)
    
    # Create a new figure with adjusted size
    fig, ax = plt.subplots(figsize=(width, height))
    ax.text(0.5, 0.5, latex_code, fontsize=10, ha='center', va='center')
    ax.axis('off')  # Hide axes

    # Save the figure as PNG with minimal white space
    try:
        plt.savefig(output_path, format='png', bbox_inches='tight', pad_inches=0.01, dpi=300, transparent=False)
        plt.close(fig)
        app_logger.log(f"LaTeX equation saved as: {output_path}")
    except Exception as e:
        app_logger.log(f"Error rendering LaTeX equation: {e}")

def download_and_save(url, save_path):    
    global logger
    # Get the file content from the URL
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Check for HTTP errors
    except requests.exceptions.RequestException as e:
        app_logger.log(f"Error downloading the file: {e}")
        return
    
    # Write the file content to the local file system
    try:
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        app_logger.log(f"File saved as: {save_path}")
    except IOError as e:
        app_logger.log(f"Error saving the file: {e}")

def svg_to_cached_png(svg_filepath):
    global logger, app
    # Ensure the file has .svg extension
    if not svg_filepath.endswith(".svg"):
        app_logger.log("Error: The input file must be an SVG file.")
        return
    
    # Create the output PNG file path
    file_name = svg_filepath.split('/')[-1]
    png_filepath = os.path.join(CACHE_DIR, '.'.join(file_name.split('.')[:-1]) + '.png')
    
    error = ''
    try:
        # Convert SVG to PNG and save it
        cairosvg.svg2png(url=svg_filepath, write_to=png_filepath)
        #app_logger.log(f"Converted PNG saved as: {png_filepath}")
    except Exception as e:
        error = e
        app_logger.log(f"Error during conversion: {error}")
        app.notify(str(e), title='SVG Error', severity='error')
    return [png_filepath, error]

def augment_img_path(path:str):
    global logger
    """
    This function converts local image paths to global image paths, if an image path is a weblink, then it is cached and the path of cached img is returned
    """
    if path.startswith('/'):
        return path # already an absolute path
    elif path.startswith('http') or path.startswith('www'):
        #h = hashlib.new('sha256')#sha256 can be replaced with diffrent algorithms
        #h.update(path.encode()) #give a encoded string. Makes the String to the Hash 
        format = path.split('.')[-1]
        local_path = os.path.join(CACHE_DIR, f'{quick_hash(string=path)}.{format}')
        app_logger.log(f'Path = {path}')
        download_and_save(path, local_path)
        return local_path
    else: # relative path
        return os.path.join(PARENT_PATH, path)

def get_styled_element(word:str, style_state:dict)->Label:
    global app_logger
    element = Label(word) # remove last occurence of specifier when rendering
    _classes = ''
    _text_style = None
    _text_style = ' '.join([_ for _ in style_state.keys() if style_state[_]])
    _text_style = _text_style if _text_style else 'none' # If _text_style == '', then change _text_style to 'none'
    
    if 'highlight' in _text_style:
        _text_style = _text_style.replace('highlight', '').strip()
        _classes = 'inline_highlight'
    if 'error' in _text_style:
        _text_style = _text_style.replace('error', '').strip()
        _classes = 'inline_error'
    if _text_style:    
        element.styles.text_style = _text_style
    element.classes = ' '.join([_classes, 'md_line_block'])
    app_logger.log(_text_style)
    return element, style_state

def finish_md_line():
    global CURRENT_ROW_MD_CONTENT_WIDTH, CURRENT_ROW_WORD_LIST
    _vert_list = [Horizontal(*CURRENT_ROW_WORD_LIST, classes='md_line'),]
    CURRENT_ROW_MD_CONTENT_WIDTH = 0
    CURRENT_ROW_WORD_LIST = []
    return _vert_list

def break_subwords(subword=None):
    global CURRENT_ROW_MD_CONTENT_WIDTH, CURRENT_ROW_WORD_LIST
    '''
    This fn breaks down subwords and returns them as a list of Label elements 
    '''
    if isinstance(subword, Label):
        style, _classes = subword.styles.text_style, ' '.join(list(subword._classes))
        subword = subword.renderable
        _sub_subwords = subword.split(' ')
        app_logger.log(subword, style, _classes)
    elif isinstance(subword, str):
        _sub_subwords = subword.split(' ')
        _classes = ''
        style = 'none'
    _list = []
    for idx in range(len(_sub_subwords)):
        _ = [Label(_sub_subwords[idx], classes=f'md_word {_classes}'), Label(' ', classes=f'md_word {_classes}')]
        #if style:
        _[0].styles.text_style, _[1].styles.text_style = style, style
        _list += _
    
    # Get the vertical elements
    available_width = int(APP_SIZE[0] * (3/4)) - 10 # 10 is a buffer # units = chars
    _vert_list = []

    for _element in _list:
        #app_logger.log(_element.styles.width, str(_element.renderable))
        _element_len = len(_element.renderable)
        if CURRENT_ROW_MD_CONTENT_WIDTH + _element_len > available_width: 
            _vert_list += finish_md_line()
        CURRENT_ROW_MD_CONTENT_WIDTH += _element_len
        CURRENT_ROW_WORD_LIST.append(_element)
        
    return _vert_list #_vert_list
        

def get_inline_md_blocks(input_string:str):
    global app_logger
    md_blocks = []

    if input_string:    
        # Render inline markdown
        inline_markdown_specifiers = {'**':'bold', '*':'italic', '__':'underline', '`':'reverse', '~~':'strike', '==':'highlight', '!!':'error'}
        style_state = {'bold':False, 'italic':False, 'underline':False, 'reverse':False, 'strike':False, 'highlight':False, 'error':False}

        app_logger.log(input_string)
        
        #for word in input_string.split(' '):
        # Replace the specifiers in the word with a common mask
        word = input_string # experimental
        _mask_string = '@%mask%@'
        _masked_word = word
        _specifier_sequence = [] # Store the sequence of specifiers

        for specifier in inline_markdown_specifiers.keys():
            _masked_word = _masked_word.replace(specifier, _mask_string)
        
        _subwords = _masked_word.split(_mask_string)
        
        '''
        _ = ''
        unused_specifiers = [] # If two specifiers are found one after another, this will store specifiers that have not yet been processed
        for subword_id in range(len(_subwords)):
            subword = _subwords[subword_id]
            _ += subword
            if subword_id != len(_subwords)-1:
                if not _:   
                    specifier = word.split(_subwords[subword_id+1])[0] if _subwords[subword_id+1] else word.split(_)[-1]
                    _specifier_set = set(specifier)
                    if len(_specifier_set) > 1:
                        for _char in specifier:
                            
                else:
                    specifier = word.replace(_,'',1).split(_subwords[subword_id+1])[0] if _subwords[subword_id+1] else word.split(_)[-1]
                _ += specifier
                _specifier_sequence.append(specifier)
        '''
        _remaining_word = word
        _subword_id = 0
        while _remaining_word and _subword_id < len(_subwords):
            _subword = _subwords[_subword_id]
            _len = len(_subword)
            if _remaining_word[:2] in inline_markdown_specifiers.keys(): # remaining_word starts with a 2-letter md specifier
                _specifier_sequence.append(_remaining_word[:2])
                _remaining_word = _remaining_word[2:]
            elif _remaining_word[0] in inline_markdown_specifiers.keys(): # remaining_word starts with a 1-letter md specifier
                _specifier_sequence.append(_remaining_word[0])
                _remaining_word = _remaining_word[1:]
            elif _remaining_word[:_len] == _subword: # remaining_word starts with word
                _remaining_word = _remaining_word[_len:]
                _subword_id += 1
            else:
                app_logger.log('ERROR : cannot find specifier')
                app_logger.log(f'_remaining_word = {_remaining_word} | _subword = {_subword}')
                exit()
            
        #app_logger.log(f'Built sentence = {_}')
        
        app_logger.log(f'Specifier sequence = {_specifier_sequence}')

        if len(_subwords) >= 1:
            #md_blocks.append(Label(_subwords[0], classes='md_line_block'))
            md_blocks += break_subwords(_subwords[0])
            app_logger.log('Added element', _subwords[0]) 

        if len(_subwords) > 1:  
            for subword_id in range(len(_subwords)-1):
                subword = _subwords[subword_id+1]
                specifier = _specifier_sequence[subword_id]
                
                style_state[inline_markdown_specifiers[specifier]] = not style_state[inline_markdown_specifiers[specifier]]
                #word = word.replace(specifier, '', 1) # remove first occurence of specifier
                
                # TODO : Bold and italics styles compete with each other leading to italics where ever there is bold.
                
                # Add the word in relevant style
                element, style_state = get_styled_element(word=subword, style_state=style_state)
                #md_blocks.append(element)
                md_blocks += break_subwords(subword=element)

                if subword_id == len(_masked_word.split(_mask_string)) - 1:
                    subword = _subwords[-1]
                    style_state[inline_markdown_specifiers[specifier]] = not style_state[inline_markdown_specifiers[specifier]]
                    # TODO : Bold and italics styles complete with each other leading to italics closure where ever there is bold closure.
                    # Add the last word in relevant style
                    element, style_state = get_styled_element(word=subword, style_state=style_state)
                    #md_blocks.append(element)
                    md_blocks += break_subwords(subword=element)
        '''
        # Add a space in relevant style
        element = Label(' ')
        _classes = ''
        _text_style = ' '.join([_ for _ in style_state.keys() if style_state[_]])
        _text_style = _text_style if _text_style else 'none' # If _text_style == '', then change _text_style to 'none'
        if 'highlight' in _text_style:
            _text_style = _text_style.replace('highlight', '').strip()
            _classes += 'inline_highlight'
        if _text_style:    
            element.styles.text_style = _text_style
        element.classes = ' '.join([_classes, 'md_line_block'])
        md_blocks.append(element)
        '''
        #break
    md_blocks += finish_md_line() + [Label('', classes='md_line_block')]    # Add a dummy to prevent extra spaces # TODO : fix this issue, this should not be required
    container = Vertical(*md_blocks)
    #container = Grid(*md_blocks)
    return container

class MdRenderLine(Static):
    """A md block line widget."""
    def __init__(self, raw_line:str='', type:str=''):
        super().__init__()
        self.raw_line = raw_line if (not isinstance(raw_line, str) or not raw_line.endswith('\n')) else raw_line[:-1]
        self.type = type

    def compose(self) -> ComposeResult:
        global logger, app, node_counter, TOC_TREE, VIEW_MODE_SCREEN
        """Create child widgets"""
        if self.type == '':
            yield get_inline_md_blocks(input_string=self.raw_line)
        elif self.type == 'newline':
            yield Label(self.raw_line, classes=f'md_line newline')
        elif self.type == 'hr':
            yield Rule(line_style='ascii', classes=f'md_line hr') #Rule(classes=f'md_line hr')
        elif self.type in [f'h{heading_level}' for heading_level in range(1,7,1)]:
            element_count = node_counter.plus(self.type)
            counter = node_counter.get_counter()
            numeral = '.'.join([str(counter[f'h{_}']) for _ in range(int(self.type.replace('h','')),0,-1)][::-1])
            numeral = '.'.join([str(int(_)-1) for _ in numeral.split('.')])
            element = get_inline_md_blocks(numeral + ' ) ' + self.raw_line)
            element.classes =f'md_line {self.type}'
            _id = self.type + '_' + quick_hash(string=f'{(numeral + " " + self.raw_line).strip().lower()}')
            element.id = _id
            if self.type == 'h1' and element_count == 1:
                #element = Label(self.raw_line, classes=f'md_line {self.type}')
                #element.id = 'document_title'
                element.border_title = 'Title'
                element.add_class('document_title')
            #else:
            #    _id = quick_hash(f'{self.type}_{self.raw_line.strip().lower()}')
            #    element.id = _id
            TOC_TREE.add_heading(numeral + " " + self.raw_line, label_id=_id, screen=VIEW_MODE_SCREEN)
            app_logger.log('Reguested addition to TOC : ', numeral)
            yield element
        elif self.type=='img':
            try:
                im = get_image_container(image_path=self.raw_line, image_type=self.type, max_height=30, width_factor=width_factor) # im = Image(self.raw_line)
                yield im
            except Exception as e:
                app.notify(message=str(e), title='ERROR', severity='error')
                app_logger.log(traceback.format_exc())
                element = Label(f'{self.raw_line}\nERROR:\n{e}', classes='md_line render_error')
                element.border_title = f'Figure {node_counter.plus(self.type)}'
                yield element
        elif self.type == 'ul':
            self.raw_line = self.raw_line.split('\n')
            self.raw_line = [get_inline_md_blocks('▶ ' + _) for _ in self.raw_line]
            element = Container(*self.raw_line,)
            element.classes=f'md_line {self.type}'
            yield element
            #yield Markdown(self.raw_line, classes=f'md_line {self.type}')
        elif self.type == 'ol':
            self.raw_line = self.raw_line.split('\n')
            self.raw_line = [get_inline_md_blocks(f'{idx+1}. {self.raw_line[idx]}') for idx in range(len(self.raw_line))]
            element = Container(*self.raw_line,)
            element.classes=f'md_line {self.type}'
            yield element
            #yield Markdown(self.raw_line, classes=f'md_line {self.type}')
        elif self.type.startswith('cb-'): # Code block
            try:
                _lang = self.type.split('-')[-1]
                #app_logger.log(_lang, type(_lang))
                if _lang == 'mermaid':
                    file_name = quick_hash(string=self.raw_line) + '.png'
                    img_file_path = os.path.join(CWD, CACHE_DIR, file_name)
                    app_logger.log(f'Saved mermaid diagram to location : {img_file_path}')
                    mermaid_to_png(mermaid_code=self.raw_line, output_path=img_file_path)
                    try:
                        im = get_image_container(img_file_path, image_type=self.type, max_height=25, width_factor=width_factor)
                        '''
                        im = Image(img_file_path)
                        width, height = get_image_dims(img_file_path)
                        max_height = 25 # percent
                        width, height = width*(max_height/height)*width_factor, max_height
                        im.styles.width, im.styles.height = f'{width}', f'{height}'
                        im.add_class('img')
                        im.border_title = f'Diagram {node_counter.plus(self.type)}'
                        im.styles.align_horizontal = 'center'
                        im.styles.align_vertical = 'middle'
                        '''
                        yield im
                    except Exception as e:
                        app.notify(message=str(e), title='ERROR', severity='error')
                        app_logger.log(traceback.format_exc())
                        element = Label(f'{self.raw_line}\nERROR:\n{e}', classes='md_line render_error')
                        element.border_title = f'Figure {node_counter.plus(self.type)}'
                        yield element
                else:
                    #_language = get_language(_lang)

                    #_highlight_query = (Path(__file__).parent / f"{_lang}_highlights.scm").read_text()
                    text_area = TextArea.code_editor(text=self.raw_line)
                    #text_area.register_language(_language, _highlight_query)

                    # Switch to Java
                    text_area.language = _lang
                    text_area.read_only, text_area.show_line_numbers = True, True
                    text_area.border_title = f'( {_lang.upper()} )'
                    text_area.border_subtitle = str(len(self.raw_line.split('\n'))) + ' lines'
                    yield text_area
            except Exception as e:
                app.notify(message=str(e), title='ERROR', severity='error')
                app_logger.log(traceback.format_exc())
                yield Label(f'{self.raw_line}\nERROR:\n{e}', classes='md_line render_error')
        elif self.type.startswith('bq'):
            self.raw_line = self.raw_line.split('\n')
            self.raw_line = [get_inline_md_blocks(_) for _ in self.raw_line]
            element = Container(*self.raw_line)
            element.classes ='md_line block_quote'
            yield element
        elif self.type == 'table':
            table =  DataTable()
            table.border_title = f'Table {node_counter.plus(self.type)}'
            table.add_columns(*self.raw_line[0])
            table.zebra_stripes = True
            rows = self.raw_line[1:]
            for row_id in range(len(rows)):
                _row_cells = rows[row_id]
                #console = Console()
                # Define markdown content to be displayed in the cells
                #rendered_cells = [console.render_str(Markdown(_)) for _ in _row_cells]
                table.add_row(*_row_cells, label=str(row_id+1))
            yield table
        elif self.type == 'latex':
            file_name = quick_hash(string=self.raw_line) + '.png'
            img_file_path = os.path.join(CWD, CACHE_DIR, file_name)
            if self.raw_line.startswith('$$'):
                self.raw_line = '$$'.join(self.raw_line.split('$$')[1:])
            if self.raw_line.endswith('$$'):
                self.raw_line = '$$'.join(self.raw_line.split('$$')[:-1])
            app_logger.log(self.raw_line)
            latex_to_png(latex_code=self.raw_line, output_path=img_file_path)
            try:
                im = get_image_container(img_file_path, image_type=self.type, max_height=5, width_factor=width_factor)
                '''
                im = Image(img_file_path)
                width, height = get_image_dims(img_file_path)
                max_height = 5 # percent
                width, height = width*(max_height/height)*width_factor, max_height
                im.styles.width, im.styles.height = f'{width}', f'{height}'
                im.add_class('img')
                im.border_title = f'Equation {node_counter.plus(self.type)}'
                im.styles.align_horizontal = 'center'
                im.styles.align_vertical = 'middle'
                '''
                yield im
            except Exception as e:
                app.notify(message=str(e), title='ERROR', severity='error')
                app_logger.log(traceback.format_exc())
                element = Label(f'{self.raw_line}\nERROR:\n{e}', classes='md_line render_error')
                element.border_title = f'Equation {node_counter.plus(self.type)}'
                yield element

class MdRenderBlock(Static):
    """A md-block widget."""

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        if event.button.id == "start":
            self.add_class("started")
        elif event.button.id == "stop":
            self.remove_class("started")

    def compose(self) -> ComposeResult: 
        """Create child widgets of a stopwatch."""
        pass

class LoadingScreen(Screen):
    def compose(self) -> ComposeResult:
        yield LoadingIndicator()

class HelpScreen(Screen):
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode"), ("w", "open_in_browser", "Open In Browser"), ('d', 'documentation', 'Documentation')]
    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        
        # Get username
        username = getpass.getuser()
        Art='WELCOME\n' + text2art(username,font='random',chr_ignore=True) + '\nHOW MAY I HELP YOU?'
        yield Label(Art, classes='splash')
    
    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark
        pass

def is_path(string:str)->bool:
    return os.path.exists(string)

class ViewModeScreen(Screen):
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode"), ("w", "open_in_browser", "Open In Browser"), ("p", "print", "Print to PDF"), ("e", "switch_to_edit", "Edit Mode"), ('v', 'switch_to_view', 'View Mode'), ('h', 'help', 'Help')]
    
    def compose(self) -> ComposeResult:
        global logger, app, PARENT_PATH, md_file
        """Create child widgets for the app."""
        # Set the app to light mode
        self.dark = False

        # Add header and footers for the app
        yield Header()
        yield Footer()

        # Add Directory Tree
        with TabbedContent(id='tabs'):
            with TabPane("Directory Tree", id='dir_tree_tab'):
                gradient = Gradient.from_colors(
                    "#881177",
                    "#aa3355",
                    "#cc6666",
                    "#ee9944",
                    "#eedd00",
                    "#99dd55",
                    "#44dd88",
                    "#22ccbb",
                    "#00bbcc",
                    "#0099cc",
                    "#3366bb",
                    "#663399",
                )

                _history_options_back_btn, _history_options_reload_btn, _history_options_next_btn = Button('Back', id='history_back_btn', tooltip='Go to previous file'), Button('Reload', id='history_reload_btn', tooltip='Reload document'), Button('Next', id='history_next_btn', tooltip='Go to next file')
                _history_options = Container(_history_options_back_btn, _history_options_reload_btn, _history_options_next_btn, id='history_options_container')
                _search_box = Input(
                    placeholder="Folder Location / Query",
                    validators=[ 
                        Function(is_path, "Path not found"),  
                    ],
                    valid_empty=True,
                    value=PARENT_PATH,
                    id='search_box'
                )
                _search_box.border_title='🔍 Search'
                #_search_box.styles.border_title_color='black'
                #_search_box.styles.width='100%'
                #_validator_response = Button('', id='validator_response', disabled=True)
                
                
                _progress_update = Container(ProgressBar(id='progress_bar', gradient=gradient), id='progress_update')
                
                
                _file_options_create_btn, _folder_options_create_btn, _file_options_delete_btn = Button('+ File', id='create_file_btn', tooltip='Create File'), Button('+ Dir', id='create_folder_btn', tooltip='Create Directory'), Button('-', id='delete_file_btn', tooltip='Delete File / Folder')
                _file_options_delete_btn.border_title='CAREFULL'
                _file_options = Container(_file_options_create_btn, _folder_options_create_btn, _file_options_delete_btn, id = 'file_options_container')
                _open_in_file_manager_btn = Button('Open in File Manager', id='open_in_file_manager', tooltip='Open selected file / directory in system file manager / application.')
                _dir_tree = DirectoryTree(PARENT_PATH)
                #_dir_tree.watch_path = True
                _dir_tree.border_title='🖿 Directory Tree'
                _dir_tree.styles.border_title_color='black'
                dir_tree = ScrollableContainer(_history_options, _search_box, _progress_update, _file_options, _dir_tree, _open_in_file_manager_btn, id='dir_tree')
                #dir_tree.styles.align = ['center', 'middle']
                #dir_tree.styles.height = '100%'
                #dir_tree.styles.width = '100%'
                yield dir_tree
            with TabPane("Table of Contents", id='toc_tree_tab'):
                '''
                _search_box_toc = Input(
                    placeholder="Folder Location / Query",
                    validators=[ 
                        Function(is_path, "Path not found"),  
                    ],
                    valid_empty=True,
                    value=PARENT_PATH,
                    id='search_box_toc'
                )
                _search_box_toc.border_title='🔍 Search'
                _search_box_toc.styles.border_title_color='black'
                _search_box_toc.styles.width='100%'
                '''
                #_validator_response_toc = Button('', id='validator_response', disabled=True)
                #tree: Tree[dict] = Tree("Dune")
                tree = TOC_TREE.get_tree()
                tree.root.expand()
                '''
                _dir_tree_toc = DirectoryTree(PARENT_PATH)
                _dir_tree_toc.border_title='Table of Contents'
                _dir_tree_toc.styles.border_title_color='black'
                '''
                dir_tree_toc = ScrollableContainer(tree, id='dir_tree_toc') # _search_box_toc,
                yield dir_tree_toc
            with TabPane('Options', id='options'):
                yield Container(Button('Export to PDF',id='export_to_pdf'))
        
        #yield dir_tree
        
        # Add content to the app
        '''
        1. Open the text file.
        2. Analyse the text file line and by line and bucket lines into markdown elements
        3. Render the elements
        '''
        with open(md_file, 'r') as _:
            raw_contents = _.readlines()
        
        processed_contents = []
        _append_to_last = False
        _code_block_status = {'open':False, 'type':None}
        _latex_block_status = {'open':False}
        _table_status = {'open':False, 'cols':0}
        for raw_line_id in tqdm(range(len(raw_contents))):
            _analysed = False

            raw_line = raw_contents[raw_line_id].strip()
            
            # Check for code blocks
            if raw_line == '```' and _code_block_status['open']:
                _code_block_status = {'open':False, 'type':None} # Close Code block
                _append_to_last = False
                continue
            elif raw_line.startswith('```'):
                _code_block_status = {'open':True, 'type':raw_line.split('```')[-1] if len(raw_line) > 3 else 'txt'} # language
                _append_to_last = True
                continue 
            elif _code_block_status['open']:       
                if (processed_contents[-1][1] == f'cb-{_code_block_status["type"]}') and _append_to_last:    
                    processed_contents[-1] = [processed_contents[-1][0] + '\n' + raw_line, f'cb-{_code_block_status["type"]}']
                    _analysed = True
                    continue
                elif _append_to_last:
                    processed_contents.append([raw_line, f'cb-{_code_block_status["type"]}'])
                    _analysed = True
                    continue
            else:
                # Check for Latex BLock code blocks
                if raw_line == '$$' and _latex_block_status['open']:
                    _latex_block_status = {'open':False} # Close Code block
                    _append_to_last = False
                    _analysed = True
                    continue
                elif raw_line == '$$' and not _latex_block_status['open']:
                    _latex_block_status = {'open':True} # language
                    _append_to_last = True
                    _analysed = True
                    continue 
                elif _latex_block_status['open'] and _append_to_last:       
                    if processed_contents[-1][1] == 'latex':    
                        processed_contents[-1] = ([processed_contents[-1][0] + '\n' + raw_line, 'latex'])
                        _analysed = True
                        continue
                    else:
                        processed_contents.append([raw_line, 'latex'])
                        _analysed = True
                        continue

                # Check for h1, h2, h3, h4, h5, h6
                for counter in range(6):    
                    if raw_line.startswith(f'{"#"*(counter+1)} '):
                        processed_contents.append([raw_line.replace("#"*(counter+1), ''), f'h{counter+1}'])
                        _analysed = True
                        break
                
                # Check for tables
                if raw_line.startswith('|') and raw_line.endswith('|'):
                    next_line = raw_contents[raw_line_id+1].strip()
                    if next_line.replace('|', '').replace('-', '').strip()=='' and len(raw_line.split('|')) == len(next_line.split('|')): # Line is a table header
                        _table_status = {'open':True, 'cols':len(raw_line.split('|'))-2}
                        processed_contents.append([[raw_line.split('|')[1:-1]], 'table'])
                        _analysed = True
                        continue
                    elif raw_line.replace('|', '').replace('-', '').strip()=='': # Line is a table collar line : |--|--|
                        _analysed = True
                        continue
                    elif len(raw_line.split('|')) == len(raw_contents[raw_line_id-1].strip().split('|')): # Line is a table body row
                        app_logger.log(processed_contents[-1][0] , [raw_line.split('|')])
                        processed_contents[-1] = ([processed_contents[-1][0] + [raw_line.split('|')[1:-1]], 'table'])
                        _analysed = True
                        continue
                elif _table_status['open']:
                    _table_status = {'open':False, 'cols':0}

                # Check for Block Contents : lists (ordered, unordered), code blocks, mermaid blocks
                if raw_line[1:3] == '. ' and isinstance(int(raw_line[0]), int): # Ordered List
                    if not _append_to_last or processed_contents[-1][1] != 'ol':    
                        processed_contents.append([raw_line[3:], 'ol'])
                        _append_to_last = True
                        _analysed = True
                        continue
                    else:  
                        processed_contents[-1] = [processed_contents[-1][0] + '\n' + raw_line[3:], 'ol']
                        _analysed = True
                        continue
                elif raw_line.startswith('- '): # Unordered List
                    if not _append_to_last or processed_contents[-1][1] != 'ul':    
                        processed_contents.append([raw_line[2:], 'ul'])
                        _analysed = True
                        _append_to_last = True
                        continue
                    else:    
                        processed_contents[-1] = [processed_contents[-1][0] + '\n' + raw_line[2:], 'ul']
                        _analysed = True
                        continue
                elif raw_line.startswith('>'): # Unordered List
                    if not _append_to_last or processed_contents[-1][1] != 'bq':    
                        processed_contents.append([raw_line[2:], 'bq'])
                        _analysed = True
                        _append_to_last = True
                        continue
                    else:    
                        processed_contents[-1] = [processed_contents[-1][0] + '\n' + raw_line[2:], 'bq']
                        _analysed = True
                        continue
                
                # Check for Images
                if raw_line.startswith('![') and raw_line.endswith(')'):
                    img_path = augment_img_path(raw_line.split('(')[-1].split(')')[0])
                    if img_path.endswith('.svg'):
                        img_path, errors = svg_to_cached_png(img_path)
                        if errors:
                            app_logger.log(errors)
                            self.notify(str(errors), severity='error', timeout=10)
                    processed_contents.append([img_path, f'img'])
                    _analysed = True
                    continue
                elif raw_line.startswith('<img'):
                    img_path = raw_line.replace('<img', '').replace('>', '').split(' ')
                    for path in img_path:
                        if 'src=' in path:
                            img_path = path.replace('src=', '').replace("'", "").replace('"', '')
                            break
                    img_path = augment_img_path(img_path)
                    if img_path.endswith('.svg'):
                        img_path, errors = svg_to_cached_png(img_path)
                        if errors:
                            app_logger.log(errors)
                            self.notify(str(errors), severity='error', timeout=10)
                    processed_contents.append([img_path, f'img'])
                    _analysed = True
                    continue
            
            if raw_line == '': # Add newline
                processed_contents.append(['', 'newline'])
                _analysed = True
                continue
            elif raw_line == '---': # Add horizontal rule
                processed_contents.append(['---', 'hr'])
                _analysed = True
                continue    
            # Add anything else as plain text line
            if _analysed:
                continue
            else:
                processed_contents.append([raw_line, ''])

        rendered_contents = [MdRenderLine(raw_line, type=_type) for raw_line, _type in processed_contents] 
        container = ScrollableContainer(*rendered_contents)
        container.add_class('app_container')
        container.styles.align = ['center','middle']
        container.styles.height = '100%'
        container.styles.width = '100%'
        container.id='md_content'
        yield container
    
    '''
    def regenerate(self):
        """Clear all widgets and regenerate content."""
        for widget in self.query(Label):  # Query and remove all Label widgets
            widget.remove()
        self.compose()  # Recompose the screen's content
        self.refresh()  # Refresh to update the display

    def action_reload_screen(self):
        self.regenerate()
    '''

    def get_md_content_size(self):
        global MD_CONTENT_MAX_SIZE
        '''
        This function gets the height and width (in chars) of the md_content container, needed to render markdown
        '''
        MD_CONTENT_MAX_SIZE = [self.query_one('#md_content', ScrollableContainer).size.height, self.query_one('#md_content', ScrollableContainer).size.width]
        return MD_CONTENT_MAX_SIZE
    
    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark

    def reload_screen(self):
        global app, node_counter, TOC_TREE, VIEW_MODE_SCREEN
        app.remove_existing_screen(ViewModeScreen)
        node_counter.refresh()
        TOC_TREE = TOC() #TOC_TREE.__init__() #.refresh()
        VIEW_MODE_SCREEN = ViewModeScreen()
        app.push_screen(VIEW_MODE_SCREEN)
        app.notify("Document Reloaded", severity='information')
    
    async def get_files(self, keyword:str, directory:str):
        global app_logger
        #subprocess.run(, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        """Run a subprocess command asynchronously."""
        # Create a subprocess with asyncio
        command = ['rg', '-l', keyword, directory]
        process = await asyncio.create_subprocess_exec(
            *command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        )
        stdout, stderr = await process.communicate()  # Wait for the command to finish
        
        if stderr:
            await app_logger.async_log(f"Error: {stderr}")
        else:
            return stdout

    async def run_command(self, keyword:str, file:str) -> str:
        global SEARCH_SCREEN, search_results, app_logger
        """Run a subprocess command asynchronously."""
        # Create a subprocess with asyncio
        command = ['rg', keyword, file]
        process = await asyncio.create_subprocess_exec(
            *command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        )
        stdout, stderr = await process.communicate()  # Wait for the command to finish
        
        if stderr:
            await app_logger.async_log(f"Error: {stderr}")
        else:
            _details = DataTable(classes='search_result_lines')
            __ = safe_decode(stdout).split('\n')
            data = [(str(_), __[_],) for _ in range(len(__))]
            _details.add_columns(*['Sn', 'Appearances',])
            _details.add_rows(data)
            search_entry = Vertical(Button(file, classes='search_result_button'), _details, classes='full_text_search_result')
            #_ = SEARCH_SCREEN.compose_add_child(search_entry)
            #SEARCH_SCREEN.scroll_visible()
            search_results.append(search_entry)

    async def full_text_search(self, submitted_string:str, keyword:str, directory:str, progress_bar:ProgressBar):
        global app, app_logger, search_results
        # Search for the keyword in files
        files, results = [], []
        search_results = [Label(f' ⬤ SEARCH RESULTS : {submitted_string} ⬤ ', id='search_results_title'),]
        try:
            # Use 'ripgrep' to enumerate files recursively in the directory.
            # This command will list all files and directories without executing the search initially.
            #progress_bar.advance(1)
            await app_logger.async_log('Getting files')
            result = await self.get_files(keyword=keyword, directory=directory)
            
            #progress_bar.advance(1)
            await app_logger.async_log('Decoding output')
            # Decode output and split into lines
            files = result.decode('utf-8').strip().split('\n')
            
            #progress_bar.advance(1)
            await app_logger.async_log('Filtering files')
            # Filter out any empty strings from the list of files
            files = [f for f in files if (f and f.endswith('.md'))]
            
            # If no files are found, return
            if not files:
                #app.notify("No files matched the specified keyword.")
                await app_logger.async_log('No files matched')
                return
            
            await app_logger.async_log('Searching keyword in files')

            # Create a tqdm progress bar
            _ = 0
            for file in files:
                # Print out the results for matched lines in each file
                await self.run_command(keyword, file) #subprocess.run(['rg', keyword, file], stdout=subprocess.PIPE)
                _ += 1
                #progress_bar.advance(1/len(files))
        except Exception as e:
            await app_logger.async_log(f"An error occurred: {e}")
            await app_logger.async_log(traceback.format_exc())

    def load(self):
        global HISTORY, app_logger, md_file, PARENT_PATH
        # Load screen to current path
        md_file = HISTORY.get_path()
        PARENT_PATH = str(Path(md_file).parent.absolute())
        self.reload_screen()

    @on(Button.Pressed)
    def create_delete_file_or_folder(self, event: Button.Pressed) -> None:
        global app, PARENT_PATH, HISTORY
        button_id = event.button.id
        file_or_folder = self.query_one('#search_box').value
        if button_id == 'create_folder_btn':
            if os.path.exists(file_or_folder) and os.path.isdir(file_or_folder):
                app.notify(f'Folder already exists : {file_or_folder}', severity='info', title='Folder Exists')
            else:
                try:
                    os.mkdir(file_or_folder)
                    app.notify('Created Folder')
                except Exception as e:
                    app.notify(str(e), severity='error', title='Exception Encountered')
        elif button_id == 'create_file_btn':
            if os.path.exists(file_or_folder) and os.path.isfile(file_or_folder):
                app.notify(f'File already exists : {file_or_folder}', severity='info', title='File Exists')
            else:
                try:
                    with open(file_or_folder, 'w') as _:
                        _.write('')
                    app.notify('Created File.')
                except Exception as e:
                    app.notify(str(e), severity='error', title='Exception Encountered')
        elif button_id == 'delete_file_btn':
            if not os.path.exists(file_or_folder):
                app.notify(f'File / folder does not exist : {file_or_folder}', severity='info', title='Does NOT Exist')
            else:
                try:
                    file_or_folder_name = file_or_folder.split('/')[-1]
                    shutil.move(file_or_folder, os.path.join(CACHE_DIR, '.trash', file_or_folder_name))
                    #os.remove(file_or_folder)
                    app.notify('File / Folder Moved To Trash')
                except Exception as e:
                    app.notify(str(e), severity='error', title='Exception Encountered')
        elif button_id == 'open_in_file_manager':
            if os.path.exists(file_or_folder):    
                os.system(f'xdg-open {file_or_folder}')
                app.notify('Opened in System Application')
        elif button_id == 'history_reload_btn':
            self.reload_screen()
        elif button_id == 'history_back_btn':
            # Set history
            HISTORY.previous()
            self.load()
        elif button_id == 'history_next_btn':
            # Set history
            HISTORY.next()
            self.load()

        _dir_tree = self.query_one(DirectoryTree)
        _dir_tree.path = Path(PARENT_PATH)
        _dir_tree.refresh()

    @on(Tree.NodeSelected)
    def on_click(self, event:Tree.NodeSelected):
        scrollable_container = self.query_one(f'#md_content', ScrollableContainer)
        # Find the Label with the specific id, e.g., "label-20"
        target_label = self.query_one("#" + event.node.data, Label)
        app_logger.log('Event node data = ', event.node.data)
        
        # Scroll to bring the target label into view
        if target_label:
            scrollable_container.scroll_to_widget(target_label)
    '''
    @on(Input.Changed)
    def show_invalid_reasons(self, event: Input.Changed) -> None:
        # Updating the UI to show the reasons why validation failed
        _button = self.query_one('#validator_response')
        if not event.validation_result.is_valid:  
            _button.disabled = True
            _button.label = str(event.validation_result.failure_descriptions)
        else:
            _button.disabled = False
            _button.label = 'Nothing'
        _button.refresh()
    '''
    @on(Input.Submitted)
    async def on_event_submitted(self) -> None:
        # Updating the UI to show the reasons why validation failed
        global app_logger, app, SearchModeScreen
        _submitted_string = self.query_one(Input).value
        
        progress_box = self.query_one('#progress_update', Container)
        progress_bar = progress_box.query_one('#progress_bar', ProgressBar)
        progress_bar.update(total=4)
        if '?' in _submitted_string:
            # Search keyword in files / current file
            if _submitted_string.startswith('?'):
                app.notify('Search folder not specified.', severity='warning')
            elif len(_submitted_string.split('?')) > 2:
                app.notify('Search query should have only one "?".', severity='warning', title='Invalid Search')
            elif len(_submitted_string.split('?')) == 2:
                app.notify('Switching to Search view.')
                directory, keyword = _submitted_string.split('?')
                await self.full_text_search(submitted_string=_submitted_string, keyword=keyword, directory=directory, progress_bar=progress_bar)
            search_screen = SearchModeScreen()
            app.push_screen(search_screen)
        elif os.path.exists(_submitted_string):
            self.query_one(DirectoryTree).path = _submitted_string
        else:
            app.notify('Invalid path / search query.', severity='warning', title='Invalid Search')

    @on(DirectoryTree.FileSelected)
    def open_file(self, event: DirectoryTree.FileSelected) -> None:
        global app, md_file, PARENT_PATH
        if str(event.path).split('.')[-1] in ['md', 'xmd']:
            app.notify(f'Loaded new file : {event.path}', title='New File Loaded')
            HISTORY.add(str(event.path))
            self.load()
        else:
            os.system(f'xdg-open {event.path}')
        self.query_one(Input).value = str(event.path)
    
    @on(DirectoryTree.DirectorySelected)
    def open_folder(self, event: DirectoryTree.DirectorySelected) -> None:
        global app
        self.query_one(Input).value = str(event.path)
        # TODO : if index.md exists within the folder, we can open the index.md 

    def action_switch_to_edit(self) -> None:
        """Action to switch to Edit Mode."""
        global app, EDIT_SCREEN
        app.remove_existing_screen(EditModeScreen)
        EDIT_SCREEN = EditModeScreen()
        app.push_screen(EDIT_SCREEN)
        app.notify("Switched to Edit Mode", severity='information')

class SearchModeScreen(Screen):
    BINDINGS = [('escape', 'switch_to_view', 'Back to View Mode')]
    
    def action_switch_to_view(self) -> None:
        """Action to switch to View Mode."""
        global app, search_results #, TOC_TREE, VIEW_MODE_SCREEN
        #switch_mode("view_mode")
        app.remove_existing_screen(SearchModeScreen)
        search_results = []
        #node_counter.refresh()
        #TOC_TREE = TOC()
        #VIEW_MODE_SCREEN = ViewModeScreen()
        #app.push_screen(VIEW_MODE_SCREEN)
        app.notify("Switched to View Mode", severity='information')

    def compose(self):
        global search_results
        yield Header()
        yield Footer()
        yield ScrollableContainer(*search_results, id='search_results')

    @on(Button.Pressed)
    def on_button_pressed(self, event:Button.Pressed):
        global app, md_file, TOC_TREE, VIEW_MODE_SCREEN
        file_name = str(event.button.label)
        md_file = file_name
        #app.notify(f'Search request = {file_name}')
        app.remove_existing_screen(SearchModeScreen)
        node_counter.refresh()
        TOC_TREE = TOC()
        VIEW_MODE_SCREEN = ViewModeScreen()
        app.push_screen(VIEW_MODE_SCREEN)
        app.notify("Switched to View Mode", severity='information')


class EditModeScreen(Screen):
    BINDINGS = [('escape', 'switch_to_view', 'Back to View Mode'), ('ctrl+s', 'save', 'Save Document')]
    
    def action_switch_to_view(self) -> None:
        """Action to switch to View Mode."""
        global app, TOC_TREE, VIEW_MODE_SCREEN
        #switch_mode("view_mode")
        app.remove_existing_screen(ViewModeScreen)
        node_counter.refresh()
        TOC_TREE = TOC()
        VIEW_MODE_SCREEN = ViewModeScreen()
        app.push_screen(VIEW_MODE_SCREEN)
        app.notify("Switched to View Mode", severity='information')

    def compose(self) -> ComposeResult:    
        self.file_path = os.path.join(CWD, md_file)

        # Open the file in Gedit
        #os.system(f'gedit {file_path}')

        # Read the markdown file
        with open(self.file_path, 'r') as _:
            content = _.read()

        # Create the editor
        self.text_area = TextArea(text=content) #TextArea.code_editor(text=content)
        self.text_area.language = "markdown"
        self.text_area.read_only, self.text_area.show_line_numbers = False, True
        self.text_area.border_title = f'( Editing {self.file_path} )'
        self.text_area.border_subtitle = str(len(content.split('\n'))) + ' lines'
        self.text_area.styles.height = '100%'
        self.text_area.theme = "monokai" # "css", "vscode_dark", "github_light", "dracula"
        yield self.text_area
        yield Header()
        yield Footer()

    def on_text_area_changed(self):
        # Get the content of the text area
        content = self.text_area.text

        # Save content
        with open(self.file_path, "w") as _:
            _.write(content)
    
    '''
    def save_document(self):
        global app
        # Get the content of the text area
        content = self.text_area.text

        # Save content
        with open(self.file_path, "w") as _:
            _.write(content)

        app.notify('Document Saved', severity='information')
    '''

class MiniMark(App):
    """A Textual app to render markdown (md) documents"""

    CSS_PATH = "data/main.tcss"
    BINDINGS = [("r", "reload", "Reload Doc")]

    def __init__(self, start_screen:str='view'):
        super().__init__()
        self.start_screen = start_screen

    async def on_mount(self) -> None:
        global APP_SIZE, HISTORY
        self.action_toggle_dark()
        self.push_screen(HelpScreen())
        #self.push_screen(LoadingScreen()) # await
        
        if self.start_screen == 'view':
            HISTORY.add(md_file)  
            self.push_screen(ViewModeScreen())
        elif self.start_screen == 'help':
            pass
            #self.push_screen(HelpScreen())
        
        # Get App size
        APP_SIZE = list(self.screen.size)

    async def on_resize(self, event):
        global APP_SIZE
        APP_SIZE = list(event.size)
        #print(f"Resized: {new_width}x{new_height} characters")

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        #self.dark = not self.dark
        pass

    def action_reload(self):
        """Replace the screen with a fresh instance."""
        global node_counter
        self.remove_existing_screen(ViewModeScreen)
        self.push_screen(ViewModeScreen())  # Push a new instance of the screen
        node_counter.refresh()
        self.notify("Content Refreshed!")
    
    def remove_existing_screen(self, screen_class):
        """Check and remove any existing instances of the screen class from the stack."""
        for screen in self.screen_stack:
            if isinstance(screen, screen_class):
                self.pop_screen()  # Remove the screen from the stack


def main():
    global CWD, PARENT_PATH, app_logger, app, print, TOC_TREE, node_counter, width_factor, VIEW_MODE_SCREEN, HELP_SCREEN, EDIT_SCREEN, SEARCH_SCREEN, search_results, _trash_dir, md_file, CACHE_DIR, HISTORY
    
    CWD = get_cwd() #os.getcwd()

    parser = argparse.ArgumentParser(description='A robust CLI app to render static markdown')
    parser.add_argument('-file', help='Location of the markdown file to render', default='')
    args = parser.parse_args()
    md_file = args.file
    if md_file:
        if not os.path.isfile(md_file):
            # Create empty file
            with open(md_file, 'w') as _:
                _.write('')
        PARENT_PATH = CWD if '/' not in md_file else '/'.join(md_file.split('/')[:-1])
        app = MiniMark()
    else:
        md_file = './help.md'
        PARENT_PATH = CWD
        app = MiniMark()
    
    CACHE_DIR = create_dir(os.path.join(CWD,'.cache'), overwrite=False) # returns a string
    _trash_dir = os.path.join(CACHE_DIR, '.trash')

    # Initialise doc tree
    TOC_TREE = TOC()
    HISTORY = history()

    # Initialise logger
    app_logger = logger()
    print = app_logger.log 

    # Node counter
    node_counter = NodeCounter()

    # Height factor
    width_factor = 2.1

    # Initialise all Screens
    VIEW_MODE_SCREEN = ViewModeScreen()
    HELP_SCREEN = HelpScreen()
    EDIT_SCREEN = EditModeScreen()
    SEARCH_SCREEN = SearchModeScreen()

    # If cache directory does not exist, create it, else clean it
    if not os.path.isdir(CACHE_DIR):
        os.mkdir(CACHE_DIR)
    else:
        shutil.rmtree(CACHE_DIR)
        os.mkdir(CACHE_DIR)

    if not os.path.isdir(_trash_dir):
        os.mkdir(_trash_dir)

    search_results = [] # This will store all search results before rendering

    app.run()

if __name__ == '__main__':
    main()