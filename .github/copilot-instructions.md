- you are running in a devcontainer
  - never create a virtual environment
  - installing packages globally is fine

- when creating a .ipynb notebook, always add 
    %load_ext autoreload
    %autoreload 2

    import sys
    sys.path.append("/workspaces/SebastianBot")
  in the first cell to fix imports