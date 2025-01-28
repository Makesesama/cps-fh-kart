{
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
  inputs.systems.url = "github:nix-systems/default";

  outputs =
    { nixpkgs, systems, ... }:
    let
      eachSystem = nixpkgs.lib.genAttrs (import systems);
      pkgsFor = eachSystem (
        system:
        import nixpkgs {
          localSystem = system;
        }
      );
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

          gpxpy

          pipx
        ];
    in
    {
      devShells = eachSystem (system: {
        default = pkgsFor.${system}.mkShell {
          packages = with pkgsFor.${system}; [
            (python312.withPackages pythonPackages)
            ruff
            qt5.full
            qt5.wrapQtAppsHook
            libsForQt5.qt5.qtwebengine
          ];
        };
      });
    };
}
