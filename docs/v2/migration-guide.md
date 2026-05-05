# Migration Guide

Herbie v2 introduces several architectural improvements and API changes. Most workflows remain similar, but a few key parameters and patterns have changed.

This guide highlights the most common changes and how to update existing code.

---

# Key API Changes

| Change                       | v1                          | v2                                    |
| ---------------------------- | --------------------------- | ------------------------------------- |
| Forecast lead time parameter | `fxx`                       | `step`                                |
| Default data directory       | `~/data/` or user specified | `~/herbie-data/`                      |
| DataFrame library            | Pandas                      | Polars                                |
| Model access                 | `Herbie(model='hrrr')`      | `Herbie.HRRR()`                       |
| Notebook display             | Plain text repr             | Rich HTML display                     |
| Inventory filtering          | Search string               | Search strong _or_ Polars expressions |
| Multi-hypercube datasets     | Flattened                   | `xarray.DataTree`                     |

---

# Common Workflows

## Create a Herbie Object

### v1

```python
from herbie import Herbie

H = Herbie(
    "2025-01-01",
    model="hrrr",
    fxx=12
)
```

### v2

```python
from herbie.v2 import HRRR

H = HRRR(
    "2025-01-01",
    step=12
)
```

Or via the namespace:

```python
from herbie.v2 import Herbie

H = Herbie.HRRR("2025-01-01", step=12)
```

---

# Forecast Lead Time

The `fxx` parameter has been renamed to `step`.

### v1

```python
H = Herbie("2025-01-01", model="hrrr", fxx=6)
```

### v2

```python
H = HRRR("2025-01-01", step=6)
```

You can also use a `timedelta`.

```python
from datetime import timedelta

H = HRRR("2025-01-01", step=timedelta(hours=6))
```

---

# Inventory

Inventories are now **Polars DataFrames**, which support fast expression-based filtering.

### v1

```python
H.inventory("TMP:2 m")
```

### v2

```python
inv = H.inventory()

inv.filter(
    pl.col("variable") == "TMP"
)
```

Benefits:

- faster performance
- flexible filtering
- access to source metadata

---

# Download Fields

### v1

```python
H.download("TMP:2 m")
```

### v2

```python
H.download("TMP:2 m")
```

The basic workflow is unchanged, but downloads now:

- run subsets in **parallel threads**
- display **Rich progress bars**
- preserve the **remote file path structure**

---

# Load Data with xarray

### v1

```python
ds = H.xarray("TMP:2 m")
```

### v2

```python
ds = H.xarray("TMP:2 m")
```

If multiple hypercubes are present, v2 returns an **xarray DataTree** rather than flattening them.

---

# Checking Data Availability

### v1

Source checking was mostly implicit.

### v2

You can explicitly resolve sources.

```python
H.resolve()
```

Check a specific source:

```python
H.resolve("google")
```

Check all sources:

```python
H.resolve("all")
```

---

# FastHerbie Changes

`FastHerbie` has been redesigned.

### v1

Focused primarily on downloading many files quickly.

### v2

Now enables **building custom GRIB files from multiple model runs**.

Example use cases:

- combine all `TMP:2 m` forecasts for a day
- combine all `GRD:10 m` forecasts initialized at one cycle

This allows users to generate **custom GRIB datasets tailored to their workflow**.

---

# Configuration

Herbie v2 introduces a **configuration file**.

This allows you to set preferences such as:

- default data directory
- preferred sources
- authentication settings

Without modifying Python code.

---

# Notebook Experience

When displayed in a Jupyter notebook, a Herbie object now shows a **rich HTML summary** that includes:

- model configuration
- forecast step
- available sources
- data availability

This makes exploratory analysis much easier.

---

# Summary

Most workflows require **minimal code changes**, but the following updates are recommended:

1. Replace `fxx` with `step`
2. Import models from `herbie.v2`
3. Update inventory workflows to use **Polars expressions**
4. Be aware that multi-hypercube datasets now return **DataTree objects**

These changes provide:

- faster performance
- improved data handling
- better extensibility
- a more modern Python API
