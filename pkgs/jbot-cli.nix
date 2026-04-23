{
  pkgs,
  lib,
  scripts,
}:
let
  jbotPython = (
    pkgs.python3.withPackages (ps: [
      ps.jinja2
      ps.pytest
      ps.pytest-mock
      ps.pytest-cov
    ])
  );
in
pkgs.stdenv.mkDerivation {
  pname = "jbot-cli";
  version = "1.2.1";
  src = scripts;
  nativeBuildInputs = [ pkgs.makeWrapper ];
  buildInputs = [ jbotPython ];
  dontBuild = true;
  installPhase = ''
    mkdir -p $out/bin
    cp -r . $out/scripts
    makeWrapper ${jbotPython}/bin/python3 $out/bin/jbot \
      --add-flags "$out/scripts/jbot_cli.py" \
      --set PYTHONPATH "$out/scripts"
  '';

  passthru = {
    python = jbotPython;
  };

  meta = with lib; {
    description = "JBot Centralized CLI and Agent Runner";
    license = licenses.mit;
    platforms = platforms.unix;
  };
}
