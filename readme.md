# Selectives Web

Who:
arthurweinberger@gmail.com
sarah.y.moffatt@gmail.com
omeydbray@gmail.com

commands cookbook

# run the application locally
. run.sh

# stop the local application
killall python

# deploy to google
~/programming/appengine/google_appengine/appcfg.py update ~/programming/appengine/selectives-web

# upload code to github
git remote add origin https://github.com/arthurw9/selectives-web.git
git push -u origin master
