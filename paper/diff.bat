@echo off

pushd ../../

if exist diff goto diff
mkdir diff
cd diff
git init
git remote add -f origin https://github.com/niklascp/bus-arrival-convlstm.git
git config core.sparseCheckout true
echo paper/* >> .git/info/sparse-checkout

:diff
git checkout tags/draft1

popd

latexdiff ..\..\diff\paper\paper.tex paper.tex > diff.tex --encoding utf8