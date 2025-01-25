{
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs =
    { nixpkgs, ... }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      pythonPackages =
        p: with p; [
          python-lsp-server
          pylsp-mypy
          pyls-isort
          python-lsp-ruff

          pyqt5
          pyserial
          msgpack
          msgspec

          pyxdg

          pyqt5
          pyqtwebengine
          folium
        ];
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        packages = [
          (pkgs.python312.withPackages pythonPackages)
          pkgs.ruff
          pkgs.qt5.full
          pkgs.qt5.wrapQtAppsHook
          pkgs.libsForQt5.qt5.qtwebengine
        ];
      };
    };
}
