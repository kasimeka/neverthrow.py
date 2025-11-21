{
  nixConfig.bash-prompt-prefix = ''(neverthrow) '';
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixpkgs-unstable";
    systems.url = "github:nix-systems/default";
  };

  outputs = inputs: let
    forAllSystems = f:
      inputs.nixpkgs.lib.genAttrs
      (import inputs.systems)
      (system: f inputs.nixpkgs.legacyPackages.${system});
  in {
    devShells = forAllSystems (pkgs: {
      default = pkgs.mkShell {
        packages = with pkgs; [
          basedpyright
          ruff
          python314
        ];
        shellHook = ''
          [ -d .venv ] && . .venv/bin/activate || {
              python -m venv .venv && . .venv/bin/activate
          }
        '';
      };
    });
  };
}
