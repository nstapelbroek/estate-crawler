# Estate Crawler

Finding a place to live can be tough. If for any reason you are unable 
to buy an house, the search for a rental apartment can cost you a lot 
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
make run
```

By default, this will output all results to a `results.json` file in the build folder. You are able to configure this
path by changing the `FEED_URI` environment variable. Other configurations are readable in the crawler.py file.