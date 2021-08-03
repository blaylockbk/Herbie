==============
🛠 Configure
==============

Some default settings are set in the ``config.toml`` file. This file is automatically created the first time you import a Herbie module and is located at ``${HOME}/.config/herbie/config.toml``. The configuration file is written in `TOML format <https://toml.io/en/>`_.

The default settings are 

.. code-block::

    [default]
    save_dir = "${HOME}/data"
    priority = [ "aws", "nomads", "google", "azure", "pando", "pando2",]

save_dir
    Default location downloaded files are saved. May use environment variables to specify directory paths. Can overwrite when creating a Herbie object.

priority
    Default data source search order, listed in order of priority. Can overwrite when creating a Herbie object.

