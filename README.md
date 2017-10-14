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

## Quick start
You can run the estate crawler by executing the crawler.py file. Below is an example that uses make as a taskrunner
to install dependencies and run the crawler.

```bash
make install
./crawler.py --region amsterdam,rotterdam,arnhem
```

By default this will output all results to a `results.json` file in the build folder. You are able to configure this
path by adding an `--output-file` argument. Other arguments are listed when issuing `--help`.

### Docker
If you have the luxury of Docker available on your system, you can run the crawler without installing any dependencies like so:
```bash
docker run --rm -it --name my-crawler-instance -v $(pwd):/app/build docker.io/nstapelbroek/estate-crawler --region amsterdam
```
Because we're mounting your current directory in /app/build, there should be a results.json file available after a successful run.
