# Firmware Finder -- _a_ _better_ _way_ _to_ _firmware_

## Intent
To make it easy to find the latest release and hotfix firmware for any product.

### Why
When using the two currently available firmware sites:
* Searching firmware gives unpredictable results
* No way to search README files in firmware
* Difficult to know which FG is related 
* Inconsistent presentation
* No historical information
* No notifications generated when updates are added


### Concepts

There are some arbitrary names for concepts used in the system.


* Brand
    * Description
        * A commercial brand
    * Example
        * AMX

* FG Number
    * Description
        * A manufacture number 
        * These have no set pattern however typically contain FG

* Product
    * Description
        * An product produced and with a brand
        * Products have one or more FG numbers
    * Example
        * NX-1200

* Associated Name 
    * Description
        * An random name that is loosely associated with a product 
    * Example
        * NX Series (X200) NX/DVX/DGX Device Firmware
        
* Firmware Version 
    * Description
        * A specific version of firmware
        * Versions are applicable to one or mare FG numbers
    * Example
        * 1.6.193

### How we gather our data

* Brands
    * Manually added 

* Products, FGs, Versions

    * Extracted from [AMX Firmware](https://www.amx.com/en/firmware) Related Products 
    * Extracted from [HARMAN AMX Hotfix Firmware](https://help.harmanpro.com/docs?t=Hotfix%20firmware)
    * FG's can be read from webpages, or from README files in firmware.



## Management Commands
 * _Bootstrapping_ - used to initially build database with a base set of fg's / firmwares / products
 * _Monitoring_ - used to send emails to subscribers 

### Management Bootstrap Command _get_amx_products_

1. Goes to https://www.amx.com/en-US/firmware 
2. Gets a product from the "Related Products" column
3. Creates a product in the database using the product name _NX-1200_

### Management Bootstrap Command _get_discontinued_products_

1. Goes to https://www.amx.com/en-US/discontinued_products
2. Creates a product with an FG relation

### Management Bootstrap Command _get_all_firmwares_
    
1. Gets to every Firmware Version in the database
2. Checks if this firmware has already been downloaded 
3. Goes to the "Download url"
4. Saves this version locally
5. When this file is saved, the Readme.txt is attempted to be found
    
    * We automatically try the following: Readme.txt readme.txt README.txt 
    * Since these are saved in various ways, the Admin console allows a different filename / path to be added if the file isn't called Readme.txt
        * For example:
            * readme.txt.txt
            * N1x33A_Updater_2021-01-21-v1.15.45/README.txt

6. We then attempt to find any existing FG in the Readme file, if we find it we link this version with the FG number

### Management Command _refresh_release_notes_

* Used if any Readme path has been updated 
* Attempts again to read the readme, and associate the FG numbers
* Should be run if new FG numbers are introduced. 
* Can also be run from web admin interface


### Management Command _check_for_firmware_updates_


1. Uses Sharepoint api to pull https://help.harmanpro.com/docs?t=Hotfix%20firmware
2. Only checks firmwares named AMX
3. Adds versions for firmwares listed under Downloads, including links

4. Goes to every Product in the database
5. Goes to the specific Product page https://www.amx.com/en/products/nx-1200
6. Looks for the "Firmware" section
7. Creates a Firmware Version for each firmware found, setting the firmware name, and download link
8. Looks for the "Specifications" section
9. Attempts to extract the FG Numbers, and create an FG number for each found.
10. Associates the Product with these FG Numbers
11. Adds and associated names found to the Product

12. If we find the existing firmware, we update the _last_seen_ 
13. If we don't find the firmware, we create a new version and send an email to subscribers







