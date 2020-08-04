echo ">> Bump Version"
poetry version patch
git add pyproject.toml
git commit -m "Bump version"
poetry version
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
