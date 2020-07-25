echo ">> Checkout Main <<"
git checkout main
echo ">> Pull <<"
git rebase origin/main
echo ">> Rebase <<"
git rebase development
echo ">> Publish <<"
git push
echo ">> Checkout Development <<"
git checkout development
