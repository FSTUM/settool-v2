#!/bin/sh

#always being in top of things is good
git pull --ff-only

# init_venv.sh
if [ -d "./bin" ];then
  echo "[info] Ctrl+d to deactivate"
  bash -c ". bin/activate; exec /usr/bin/env bash --rcfile <(echo 'PS1=\"(venv)\${PS1}\"') -i"
fi

# prepare system dependencies
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv texlive-base texlive-lang-german texlive-fonts-recommended texlive-latex-extra gettext npm

# prepare python dependencies
python3 -m venv venv
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt -r requirements_dev.txt

# manage staticfiles
rm -rf mediafiles
python3 manage.py collectstatic --noinput

# setup database with mock data
rm -f db.sqlite3
python3 manage.py migrate
echo "import settool_common.fixtures.showroom_fixture;settool_common.fixtures.showroom_fixture.showroom_fixture_state_no_confirmation()"|python3 manage.py shell

# expose port 17170 to the internet
python3 manage.py runserver 0.0.0.0:17170
