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

# process for merging upstream changes
  # pull master down to a new branch: origin/master
  git fetch origin
  # switch back to master branch
  git checkout master
  # merge the upstream changes
  git merge origin/master

# stash uncommited changes in the current branch:
git add <any untracked files>
git stash

# see what's stashed
git stash list

# restore the stashed work
git stash apply

# drop the stashed work after applying
git stash drop stash@{0}

# restore a specific stash
git stash apply stash@{2}

# restore and drop the stashed work
git stash pop

# fixing a merge conflict
  git status shows that the files that merged ok are already added to 
  a change but not committed. The merge conflicts are listed separately.
  They have change markers around conflicts. Edit these manually and
  add or remove the files to the pending change then commit the change.
