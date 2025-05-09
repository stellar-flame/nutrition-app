# Fish shell configuration file

# Add Python user base binary directory to PATH
set -gx PATH /Users/hava/Library/Python/3.9/bin $PATH

# Pyenv initialization
set -Ux PYENV_ROOT $HOME/.pyenv
set -Ux PATH $PYENV_ROOT/bin $PATH

status --is-interactive; and pyenv init --path | source
status --is-interactive; and pyenv init - | source

# You can add other configurations below
