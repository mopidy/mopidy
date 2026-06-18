{
  description = "Mopidy development flake";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  inputs.pyproject-nix.url = "github:pyproject-nix/pyproject.nix";
  inputs.pyproject-nix.inputs.nixpkgs.follows = "nixpkgs";

  outputs =
    { self, nixpkgs, pyproject-nix }:
    let
      lib = nixpkgs.lib;
      forAllSystems = lib.genAttrs lib.systems.flakeExposed;
      mopidyVersion = "4.0.0";
      project = pyproject-nix.lib.project.loadPyproject {
        projectRoot = ./.;
      };
    in
    let
      perSystem =
        system:
        let
          pkgs = import nixpkgs { inherit system; };
          python = pkgs.python313;
          pyPkgs = python.pkgs // {
            pygobject = python.pkgs.pygobject3;
            rumdl = pkgs.rumdl;
            zensical = pkgs.zensical;
          };

          mopidyAttrs = project.renderers.buildPythonPackage {
            inherit python;
            pythonPackages = pyPkgs;
            inherit project;
          };

          mopidy = pyPkgs.buildPythonApplication (
            mopidyAttrs
            // {
              version = mopidyVersion;

              nativeBuildInputs = (mopidyAttrs.nativeBuildInputs or [ ]) ++ [
                pkgs.wrapGAppsNoGuiHook
              ];

              preBuild = (mopidyAttrs.preBuild or "") + ''
                export SETUPTOOLS_SCM_PRETEND_VERSION=${mopidyVersion}
              '';
            }
          );

          pythonEnv = python.withPackages (
            ps:
            (project.renderers.withPackages {
              inherit python;
              pythonPackages = pyPkgs;
              inherit project;
              groups = [
                "docs"
                "rumdl"
                "ruff"
                "tests"
              ];
            } ps)
            ++ [
              ps.tox
              ps.ty
              ps."pygobject-stubs"
            ]
          );

          gstreamerRuntime = with pkgs.gst_all_1; [
            gstreamer
            gst-plugins-base
            gst-plugins-good
          ] ++ [
            pkgs.glib-networking
            pkgs.gobject-introspection
          ];

          cairoBuildInputs = [
            pkgs.cairo
            pkgs.libxcb
            pkgs.libx11
            pkgs.xorgproto
          ];

          cairoIncludePath = pkgs.lib.makeSearchPathOutput "dev" "include" cairoBuildInputs;
          cairoIncludeFlags = lib.concatMapStringsSep " " (path: "-I${path}") (
            lib.splitString ":" cairoIncludePath
          );
        in
        {
          packages = {
            default = mopidy;
            mopidy = mopidy;
            pythonEnv = pythonEnv;
          };

          devShells.default = pkgs.mkShell {
            packages = [
              mopidy
              pythonEnv
            ] ++ gstreamerRuntime ++ [
              pkgs.cairo
              pkgs.libxcb
              pkgs.meson
              pkgs.ninja
              pkgs.pkg-config
              pkgs.pyright
              pkgs.python314
              pkgs.uv
              pkgs.libx11
              pkgs.xorgproto
            ];

            env = {
              UV_NO_MANAGED_PYTHON = "1";
              UV_PYTHON_DOWNLOADS = "never";
            };

            shellHook = ''
              export CPATH="${cairoIncludePath}''${CPATH:+:$CPATH}"
              export CFLAGS="${cairoIncludeFlags} ''${CFLAGS:+$CFLAGS}"
              export CPPFLAGS="${cairoIncludeFlags} ''${CPPFLAGS:+$CPPFLAGS}"
              export NIX_CFLAGS_COMPILE="${cairoIncludeFlags} ''${NIX_CFLAGS_COMPILE:+$NIX_CFLAGS_COMPILE}"
              export PYTHONPATH="$PWD/src:${mopidy}/${python.sitePackages}''${PYTHONPATH:+:$PYTHONPATH}"
              export GI_TYPELIB_PATH="${pkgs.lib.makeSearchPathOutput "lib" "lib/girepository-1.0" gstreamerRuntime}''${GI_TYPELIB_PATH:+:$GI_TYPELIB_PATH}"
              export GST_PLUGIN_SYSTEM_PATH_1_0="${pkgs.lib.makeSearchPathOutput "lib" "lib/gstreamer-1.0" gstreamerRuntime}''${GST_PLUGIN_SYSTEM_PATH_1_0:+:$GST_PLUGIN_SYSTEM_PATH_1_0}"
            '';
          };
        };
    in
    {
      packages = forAllSystems (system: (perSystem system).packages);
      devShells = forAllSystems (system: (perSystem system).devShells);
    };
}
