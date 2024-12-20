#!/bin/bash

for file in "$@"; do
        name=$(basename $file .swc)
        echo -n "normalizing $name ... "
        soma=$(grep -v '#' $file | head -n 1 | awk "{print(\$6)}")
        dist=$(swc measure $file -p 3 | grep dist | awk "{print(\$3)}")
        scale=$(echo "100.0 / ( $dist + $soma )" | bc -l)
        swc modify $file -s $scale $scale $scale -o $name-norm.swc
        echo done
done
