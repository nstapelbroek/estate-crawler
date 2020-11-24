# Estate Crawler

Finding a place to live can be tough. If for any reason you are unable 
to buy a house, the search for a rental apartment can cost you a lot 
of time and money. Real estate agencies will often charge you before
you've even visited your first potential "object". 
The subscriptions they force upon you are unfair and do not 
guarantee success of finding a place to live.

This project aims to relieve some pain by giving you insights of the 
offers at several agencies. By collecting and comparing this data, 
you can pick an agency that is best suited for your needs. 
Saving you time and potentially money.

# Usage
You can run the estate crawler by executing the crawler.py file. Below is an example with Python3 and pipenv installed on your OS:

```bash
pipenv install && pipenv run ./crawler.py --region amsterdam,rotterdam,arnhem
```

If you have the luxury of Docker available on your system, you can run the crawler without installing any dependencies like so:
```bash
docker run --rm -v $(pwd):/app/build docker.io/nstapelbroek/estate-crawler --region amsterdam
```

Results of your crawl run are available in ./build/results.json after a successful run. You can change this path by passing
a `--output-file` argument. Note that the output file does not contain valid json, only valid json lines. 