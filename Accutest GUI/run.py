import os
import sys

src_path = os.path.join(os.path.dirname(__file__), "src")
sys.path.insert(0, src_path)

from main import main

if __name__ == "__main__":
    main()