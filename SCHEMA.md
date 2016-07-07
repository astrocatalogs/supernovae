This document describes the standard Open Supernova Catalog (OSC) JSON format. For JSON files in this repository, which are mostly entered by hand (often via the edit icon on the main table page) or via direct data donations, our format requirements are less strict than usual, for instance if you forget to set a supernova's name field, our import script is smart enough to do this for you. As JSON is a sparse format, object names that don't follow our default name choices will simply be ignored by the script. In most cases, this is not desirable as you will want your data to be readable by the catalog import script, but it can be useful for adding new objects that may be unique to your dataset, which in the future could be parsed by the catalog. But so long as you are only adding standard data to a supernova, it is best to follow the guidelines set in this document as closely as possible to avoid potential issues.

Each supernova is contained with a single JSON file that contains a single object bearing the supernova's primary name, which when empty represents the minimum readable entry file:

```JSON
{
	"SN1987A":{}
}
```

To comply with the standard, the object should contain a `schema` key, where `schema` is a permanent URL to the version of this document defining the file's schema (with `commithash` replaced appropriately), and a `name` key, where the `name` key should be identical to the object field name:

```JSON
{
	"SN1987A":{
		"schema":"https://github.com/astrocatalogs/sne/blob/commithash/OSC-JSON-format.md",
		"name":"SN1987A"
	}
}
```

As JSON is a serialized format, *field order does not matter*, but the OSC's import scripts will automatically organize the data in the output JSON files to make them more readable (for instance we sort photometry and spectra within each file by date, the data quantity fields by name, etc.).

Sources are extremely important in the OSC, and every single piece of data added to an event JSON file **must have a source attribution**, with the sole exception of the supernova name, aliases, and the sources themselves. Published data sources are preferred over secondary sources (the OSC falls into a secondary source category), but if the data was collected by a secondary source intermediate to being added to the OSC, these sources should also be attributed in the source list.

Sources of data contain five fields, three of which are optional:

| Field | Value | Optional?
| :--- | :--- | :---
`name` | Source name, e.g. "Catchpole et al. 1989" | no
`alias` | Integer unique to this source to be used as an alias | no
`url` | Web address of source | yes
`bibcode` | 19 character NASA ADS bibcode | yes
`secondary` | Boolean specifying if source collected rather than generated data | yes
`acknowledgment` | Acknowledgment requested by source if data is used in publication | yes

The sources object contains an array of such objects:

```JSON
"sources":[
	{
		"name":"Catchpole et al. (1987)",
		"bibcode":"1987MNRAS.229P..15C",
		"alias":"1"
	},
	{
		"name":"SUSPECT",
		"url":"https://www.nhn.ou.edu/~suspect/",
		"alias":"2",
		"secondary":true
	}
]
```

The OSC stores many different pieces of metadata for each event. Data quantities are added to each event as arrays of objects, with each piece of datum being tagged with its associated sources' alias tags. As an example a redshift object array may look like:

```JSON
"redshift":[
	{
		"value":"0.045",
		"error":"0.001",
		"source":"1,2",
		"kind":"heliocentric"
	},
	{
		"value":"0.043",
		"error":"0.002",
		"source":"3",
		"kind":"host"
	}
]
```

where in this example we have two different redshift values quoted from three different sources, where two of the sources agree with one another, and the third source actually refers to the redshift of the host galaxy rather than the supernova. Note that all the numerical quantities are stored as strings instead of as numbers, the OSC's policy is to store the data with exactly the same number of significant digits as the sources that provide them, and storing the importing the data as floating point numbers can often introduce small floating-point errors that we wish to avoid.

Data quantities have five standard fields:

| Field | Value | Optional?
| :--- | :--- | :---
| `value` | The value of the quantity | no
| `error` | The error associated with the value | yes
| `lowerlimit` | Value is a lower limit | yes
| `upperlimit` | Value is an upper limit | yes
| `unit` | The unit of the value | yes
| `kind` | Variant of the quantity | yes
| `source` | A list of integer aliases to sources for the data | no

Currently, the OSC explicitly tracks the following quantities for each event, if available:

| Quantity | Description | Kinds
| :--- | :--- | :---
| `alias` | Other names this supernova goes by |
| `distinctfrom` | Names of events SN is *not* associated with, usually very nearby supernovae that may be confused with the given supernova |
| `error` | Known errors in sources of data that are ignored on import |
| `ra` | Right ascension of supernova in hours (`hh:mm:ss`) |
| `dec` | Declination of supernova in degrees |
| `discoverdate` | Date that the supernova was first observed |
| `maxdate` | Date of the supernova's maximum light |
| `redshift` | Redshift of supernova or its host in various frames | `heliocentric`, `cmb`, `host`
| `lumdist` | Luminosity distance to the supernova |
| `comovingdist` | Comoving distance to the supernova |
| `velocity` | Recessional velocity of supernova | `heliocentric`, `cmb`, `host`
| `claimedtype` | Claimed type of the supernova |
| `discoverer` | Person(s) who discovered the supernova |
| `ebv` | Reddening originating from the Milky Way |
| `host` | Host galaxy of the supernova |
| `hostra` | Right ascension of the host galaxy in hours (`hh:mm:ss`) |
| `hostdec` | Declination of the host galaxy in degrees |
| `hostoffsetang` | Offset angle between host and supernova |
| `hostoffsetdist` | Offset angular diameter distance between host and supernova |
| `maxappmag` | Maximum apparent magnitude |
| `maxband` | Band that maximum was determined from |
| `maxabsmag` | Maximum absolute magnitude |

Photometry and spectra are stored in a similar way, but have different and many more standard field names. Both photometry and spectra share a few fields:

| Field | Value | Optional?
| :--- | :--- | :---
| `time` | Time of observation (can be a two-element array for start/stop) | yes
| `e_time` | Error in the time | yes
| `e_lower_time` | Lower error in the time | yes
| `e_upper_time` | Upper error in the time | yes
| `u_time` | Unit for time | yes
| `survey` | Name of survey observations were collected by | yes
| `instrument` | Instrument used for observation | yes
| `telescope` | Telescope used for observation | yes
| `observatory` | Observatory used for observation | yes
| `observer` | Person(s) who conducted the observation | yes
| `reducer` | Person(s) who reduced the observation | yes
| `includeshost` | Host galaxy light not subtracted from observation | yes
| `source` | A list of integer aliases to sources for the data | no

For IR/optical/UV photometry specifically, typical field names are:

| Field | Value | Optional?
| :--- | :--- | :---
| `magnitude` | Apparent magnitude | no
| `e_magnitude` | Error in the magnitude | yes
| `e_lower_magnitude` | Lower (i.e. more negative) error in the magnitude | yes
| `e_upper_magnitude` | Upper (i.e. more positive) error in the magnitude | yes
| `band` | Photometric band filter used | yes
| `system` | Photometric system used | yes
| `upperlimit` | Measurement is an upper limit | yes
| `kcorrected` | Photometry has been K-corrected for redshift effects | yes
| `scorrected` | Photometry has been S-corrected for extinction in host galaxy | yes
| `mcorrected` | Photometry has been S-corrected for extinction from Milky Way | yes

For radio, a few more field names are used:

| Field | Value | Optional?
| :--- | :--- | :---
| `frequency` | Frequency of observation | yes
| `u_frequency` | Unit for frequency | yes
| `fluxdensity` | Flux density | no
| `e_fluxdensity` | Error in flux density | yes
| `u_fluxdensity` | Unit for flux density | yes
| `upperlimit` | Measurement is an upper limit | yes

For X-ray, the additional set of fields are:

| Field | Value | Optional?
| :--- | :--- | :---
| `energy` | Detector energy (can be a two-element array for range) | yes
| `u_energy` | Unit of energy | yes
| `flux` | Energy flux | no
| `unabsorbedflux` | Unabsorbed energy flux | yes
| `photonindex` | Power-law assumed to convert counts to flux | yes
| `counts` | Counts per second on the detector | yes
| `nhmw` | Milky Way hydrogen column density | yes
| `e_flux` | Error in the flux | yes
| `u_flux` | Unit for flux | yes
| `upperlimit` | Measurement is an upper limit | yes

And finally for spectra, these fields are used:

| Field | Value | Optional?
| :--- | :--- | :---
| `data` | Nx2 or Nx3 array of wavelengths, fluxes, and (optionally) errors | no
| `waveunit` | Unit for wavelength | no
| `fluxunit` | Unit for fluxes | no
| `snr` | Signal to noise ratio | yes
| `filename` | Name of file spectra was extracted from | yes
| `deredshifted` | Data is known to have been deredshifted from observer frame | yes
| `dereddened` | Data is known to have been dereddened | yes
| `exclude` | Suggested wavelengths (in &#8491;) to exclude when plotting/analyzing, can be `above`, `below`, or `range`, e.g. `"above":"10000"` would suggested excluding data from wavelengths greater than 10,000 &#8491;, `"range":["8000","8100"]` would suggested excluding data from wavelengths in between 8,000 and 8,100 &#8491; | yes
| `source` | A list of integer aliases to sources for the data | no

So long as it is reasonable, the OSC is open to adding more field names should additional information need to be stored in an event file beyond the quantities and data we have chosen to track here, please contact us and let us know if you have any suggestions on how the standard format can be improved.
