# devenv.nix
{ pkgs, lib, config, inputs, ... }:

let
  pythonVersion = pkgs.python314;

  xapian2 = import ./nix/xapian-2.nix {
    inherit pkgs;
    python3 = pythonVersion;
  };

  # Make a package
  xapianPythonPkg = pkgs.python314Packages.buildPythonPackage {
    pname = "xapian";
    version = "2.1.0";
    format = "other"; 
    src = xapian2.xapianBindings;
    installPhase = ''
      mkdir -p $out/lib/python3.14/site-packages
      cp -r $src/lib/python3.14/site-packages/* $out/lib/python3.14/site-packages/
    '';
  };

  pythonWithXapian = pythonVersion.withPackages (ps: [
    xapianPythonPkg
  ]);
in
{

  # https://devenv.sh/basics/
  env.GREET = "devenv";
  env.HTTPS = "off";
  env.SITH_DEBUG = "true";
  env.SECRET_KEY = "(4sjxvhz@m5$0a$j0_pqicnc$s!vbve)z+&++m%g%bjhlz4+g2";
  env.REDIS_PORT = toString config.services.redis.port;
  env.CACHE_URL = "redis://127.0.0.1:${toString config.services.redis.port}/0";
  env.TASK_BROKER_URL = "redis://127.0.0.1:${toString config.services.redis.port}/1";

  # https://devenv.sh/packages/
  packages = [ 
    pkgs.git         
    pkgs.pkg-config    
    pkgs.openssl        
    pkgs.libjpeg        
    pkgs.zlib           
    pkgs.gettext     
    pkgs.gnumake
    pkgs.gcc
  ];


  languages.python = {
    enable = true;
    package = pythonWithXapian; # use custom package.
    lsp.enable = true;
    venv.enable = true;
    uv = {
      enable = true;
      sync = {
        enable = true;
        groups = [
          "dev"
          "tests"
          "docs"
        ];
      };
    };
  };

  languages.javascript = {
    enable = true;
    lsp.enable = true;
    package = pkgs.nodejs_24;  
    npm = {
      enable = true;
      install.enable = true;
    };
  };

  services.redis = {
    enable = true;
  };

  processes = {
    server = {
      ports = {
        sith.allocate =  8000;
      };
      exec = "uv run $DEVENV_ROOT/manage.py runserver 0.0.0.0:${toString config.processes.server.ports.sith.value}";
      restart = {
        on = "always";
      };
      after = [ "devenv:processes:redis" ];
    };

    celery = {
      exec = "uv run celery -A sith worker --beat -l INFO";
      restart = {
        on = "always";
      };
      after = [ "devenv:processes:redis" ];
    };
  };

  profiles.dev = {
    module = {
      env.DATABASE_URL = "sqlite:///db.sqlite3";
      env.PROCFILE_STATIC = "Procfile.static";
    };
  };

  profiles.full =  {
    module = {

      packages = [
        pkgs.libpq
        pkgs.postgrest
      ];

      languages.python.package = lib.mkForce (pythonVersion.withPackages (ps: [
        xapianPythonPkg
        ps.psycopg
      ]));

      env.PROCFILE_STATIC = "";

      # Postgress
      services.postgres = {
        enable = true;
        initialDatabases = [
          { 
            name = "sith";
          }
        ];
        initialScript = ''
          CREATE USER sith WITH PASSWORD 'password';

          ALTER ROLE sith SET client_encoding TO 'utf8';
          ALTER ROLE sith SET default_transaction_isolation TO 'read committed';
          ALTER ROLE sith SET timezone TO 'UTC';

          GRANT ALL PRIVILEGES ON DATABASE sith TO sith;
          GRANT ALL PRIVILEGES ON SCHEMA public TO sith;
        '';
        settings = {
          listen_addresses = lib.mkForce "127.0.0.1";
        };
      };
      env.DATABASE_URL = "postgres://sith:password@127.0.0.1:${toString config.services.postgres.port}/sith";
      processes.server.after = [ "devenv:processes:redis" "devenv:processes:postgres" ];

      # Nginx 
      services.nginx = {
        enable = true;
        eventsConfig = ''
          worker_connections 1024;
        '';
        httpConfig = ''
          server {
            listen 127.0.0.1:8001;

            server_name localhost;

            # Gestion des fichiers statiques
            location /static/ {
              root ${config.devenv.root};
            }

            # Fichiers médias publics
            location ~ ^/data/(products|com|club_logos|upload)/ {
              root ${config.devenv.root};
            }

            # Fichiers médias privés/protégés
            location ~ ^/data/(SAS|profiles|users|.compressed|.thumbnails)/ {
              internal;
              root ${config.devenv.root};
            }

            # On redirige tout le reste vers Django (sur le port 8001)
            location / {
              proxy_pass http://127.0.0.1:${toString config.processes.server.ports.sith.value};
              proxy_set_header Host $http_host;
              proxy_set_header X-Real-IP $remote_addr;
              proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
              proxy_set_header X-Forwarded-Proto $scheme;
            }
          }
        '';
      };

      # Watcher for statics
      processes = {
        "watcher" = {
          exec = "uv run $DEVENV_ROOT/manage.py collectstatic --noinput";
          watch = {
            paths = [
              ./.
            ];
            extensions = [ 
              "js" 
              "css" 
              "scss"
              "ts"
            ];
            ignore = [
              ".devenv/*"
              ".git/*"
              "node_modules/*"
              "staticfiles/*"
              "static/*"
            ];
          };
        };
      };

      enterShell = ''
        psql -d sith -c "GRANT ALL PRIVILEGES ON SCHEMA public to sith";
      '';
    };
  };

  tasks = {

    # Init Prject
    "project:init" = {
      exec = ''
        uv run $DEVENV_ROOT/manage.py setup
      '';
      before = [ "tras:compile" ];
    };

    # Install Translations
    "tras:compile" = {
      exec = ''
        uv run $DEVENV_ROOT/manage.py compilemessages
      '';
    };
  };

  scripts = {

    "db:migrate" = {
      exec = ''
        uv run $DEVENV_ROOT/manage.py migrate "$@"
      '';
    };

    "db:make-migration" = {
      exec = ''
        uv run $DEVENV_ROOT/manage.py makemigrations "$@"
      '';
    };

    "db:squash" = {
      exec = ''
        uv run $DEVENV_ROOT/manage.py squasmigrations "$@"
      '';
    };

    "db:create-su" = {
      exec = ''
        uv run $DEVENV_ROOT/manage.py createsuperuser "$@"
      '';
    };

    "db:populate" = {
      exec = ''
        uv run $DEVENV_ROOT/manage.py populate "$@"
      '';
    };

    "db:populate-more" = {
      exec = ''
        uv run $DEVENV_ROOT/manage.py populate_more "$@"
      '';
    };

    "trans:make" = {
      exec = ''
        uv run $DEVENV_ROOT/manage.py makemessages --locale=fr -e py,jinja --ignore=.venv --ignore=node_modules --add-location=file 
        uv run $DEVENV_ROOT/manage.py makemessages --locale=fr -d djangojs -e js,ts --ignore=.venv --ignore=node_modules --ignore=staticfiles/generated --add-location=file
      '';
    };

    "trans:compile" = {
      exec = ''
        uv run $DEVENV_ROOT/manage.py compilemessages "$@"
        '';
    };

    "project:line-cont" = {
      exec = ''
        cloc $DEVENV_ROOT --exclude-dir=doc,env "$@"
      '';
      packages = [ pkgs.cloc ];
    };

    "project:pre-commit" = {
      exec = ''
         uv run pre-commit run 
      '';
    };

    "test:run" = {
      exec = ''
        uv run pytest "$@"
      '';
    };

    "server:anti-spam-update" = {
      exec = ''
        uv run $DEVENV_ROOT/manage.py update_spam_database "$@"
      '';
    };

    "start-pycharm" = {
      exec = ''
        2>/dev/null 1>&2 pycharm &
      '';
    };
  };

  enterTest = ''
    
  '';

  enterShell = ''
    # Create a symlink to the Python virtual environment for IDE compatibility
    if [ ! -L "$DEVENV_ROOT/venv" ]; then
        ln -s "$DEVENV_STATE/venv/" "$DEVENV_ROOT/venv"
    fi
  '';

}
