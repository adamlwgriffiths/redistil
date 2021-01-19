{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    bashInteractive
    python38Full
    python38Packages.setuptools
    python38Packages.pip
    python38Packages.virtualenv
  ];

  shellHook = ''
    YELLOW='\033[1;33m'
    NC="$(printf '\033[0m')"

    # python
    SOURCE_DATE_EPOCH=$(date +%s)  # so that we can use python wheels
    echo -e "''${YELLOW}Creating python environment...''${NC}"
    export PYTHONDONTWRITEBYTECODE="True"
    virtualenv .venv > /dev/null
    export PATH=$PWD/.venv/bin:$PATH > /dev/null
    export PYTHONPATH=$PWD/.venv/lib/python38/site-packages > /dev/null
    export PYTHONPATH=$PWD:$PYTHONPATH > /dev/null
    pip install -r requirements.txt > /dev/null

    # docker-compose
    echo -e "''${YELLOW}Start services: bin/services.start''${NC}"
    echo -e "''${YELLOW}Stop services: bin/services.stop''${NC}"

    export REDIS_URL="redis://redis@localhost:6379/0"
  '';
}
