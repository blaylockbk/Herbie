# Model Details and Source Templates

The input for this function is a Herbie object.

The source URL template is given for each source. _Model template class names should not duplicated_

For subsetting, we assume an index file is located at `<source_url>.idx`

## Possible Source

The data download source for the RAP and HRRR models.

- `'aws'` Amazon Web Services (Big Data Program)
- `'nomads'` NOAA's NOMADS server
- `'google'` Google Cloud Platform (Big Data Program)
- `'azure'` Microsoft Azure (Big Data Program)
- `'pando'` University of Utah Pando Archive (gateway 1)
- `'pando2'` University of Utah Pando Archive (gateway 2)
