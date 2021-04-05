#!/bin/sh

# init_venv.sh
if [ -d "./bin" ];then
  echo "[info] Ctrl+d to deactivate"
  bash -c ". bin/activate; exec /usr/bin/env bash --rcfile <(echo 'PS1=\"(venv)\${PS1}\"') -i"
fi

echo "Installing dependencys"
# prepare system dependencies
sudo apt-get update
sudo apt-get -qq -y install python3-pip python3-venv texlive-base texlive-lang-german texlive-fonts-recommended texlive-latex-extra gettext npm

# prepare python dependencies
python3 -m venv venv
python3 -m pip install --upgrade pip | grep -v 'already satisfied'
python3 -m pip install -r requirements.txt -r requirements_dev.txt | grep -v 'already satisfied'

# manage staticfiles
echo "Removing media and updating staticfiles"
rm -rf staticfiles
rm -rf mediafiles
python3 manage.py collectstatic --no-input

# setup database with mock data
echo "Setting up mocked database conent"
rm -f db.sqlite3
python3 manage.py migrate --no-input -v 0
echo "import settool_common.fixtures.showroom_fixture;settool_common.fixtures.showroom_fixture.showroom_fixture_state_no_confirmation()"|python3 manage.py shell

# restart gunicorn on port 17170
echo "\e[7Restarting staging server"
sudo systemctl restart gunicorn
echo "DONE"
