# Contributing
Contributing to the EDMC Plugin Registry can be done in two ways: Listing/Updating your own plugin, or joining our review team.

# Submitting a Plugin for Listing
Listing a plugin is as simple as submitting a PR with the details of a new plugin you wish to list in the plugin browser. This must be your own plugin - or a plugin you are a legitimate co-author of. You may not submit a plugin on someone else's behalf, or list a plugin you don't maintain. 

Before submitting a plugin, please review the standards in [STANDARDS.md](/docs/STANDARDS.md). Ensure that your plugin follows all of the standards expected. 

After review, and ensuring that your plugin meets all the standards, you can open a new PR. For new plugins, you will want this PR to include a new .json file with the details of the plugin you wish to list. Be sure to fill this out completely. You can view an example of the format we expect the JSON file to be in [example.json](/docs/example.json). 

### Required Fields:
The current fields expected are:
- `pluginName`: (str) The name of the plugin.
- `pluginVer`: (str) A Semantic Version compatible version string.
- `autoUpdateEnabled`: (bool) A boolean value that determines if the plugin can attempt to auto-update.
- `autoInstallEnabled`: (bool) A boolean value that determines if the plugin can attempt to automatically install itself.
- `pluginAuthors`: (list) A list of strings, where each string is an author or authorized maintainer of a plugin. 
- `pluginMainLink`: (str) A web URL for the main project page.
- `pluginLastUpdate`: (str) The date of the last plugin update.
- `pluginDirName`: (str) The directory the plugin is loaded from by default. Generally, this is the name of the plugin.
- `pluginCategory`: (list) A list of strings of which categories the plugin belongs to. Valid categories are listed below. 
- `pluginDesc`: (str) A brief description of the plugin's purpose. 
- `pluginLastTestedEDMC`: (str) The last version of EDMC this plugin was tested against. 
- `pluginLicense`: (str) The SPDX license string for your plugin's chosen license.

### Recommended Fields:
These fields will be required in order to use the upcoming Auto Update or Auto Install functionality. 
- `pluginHash`: (str) the SHA256 Hash Value of the plugin's release archive.
- `pluginZip`: (str) A link to the latest release archive of the plugin. 

### Optional Fields: 
- `pluginRequirements`: (list) A list of strings, where each string is a non-standard requirement needed for the plugin to work, or the name of another plugin required. 
- `pluginIcon`: (str) A web link to a PNG or ICO file for a plugin.
- `pluginVT`: (str) A link to the plugin's release archive upload to VirusTotal (or another similar tool).

Currently, `autoUpdateEnabled` and `autoInstallEnabled` should both be left at False, as these represent future features that are not currently available. 

Ensure that you have listed sufficient tags so that users can view what types of help your plugin provides. The current list of valid and accepted tags is: 

* Exploration
* Navigation
* Combat
* Trading
* Engineering
* Anti-Xeno
* Colonization
* Utility
* Lore
* Social
* Streaming
* Other

Plugins can have more than one category - but must have at least one category.

We have a template for PRs. Please ensure your PR follows the template to ensure it is processed quickly. ONLY submit a single JSON file under [plugins](/plugins/). Do NOT submit updates to the [Master Plugin List](/master_plugin_list.json). This file is updated automatically when your PR is accepted. 

## Updating Plugins
If you have submitted a plugin, and that submission has been accepted, you are now responsible for keeping the plugin listing up to date. 

This is relatively simple - open a new PR with the updates needed to the existing file! Only someone listed as one of the plugin authors may open a PR on an existing file. You only need to update your plugin's individual file.

We have a template for PRs. Please ensure your PR follows the template to ensure it is processed quickly. ONLY submit updates for a single JSON file under [plugins](/plugins/). Do NOT submit updates to the [Master Plugin List](/master_plugin_list.json). This file is updated automatically when your PR is accepted. 

If you have multiple plugins to update, please open a single PR for each plugin.

# Review Team
The review team are people who test plugins, review their code, and ensure that all listed plugins are working well with users' installs of EDMC. We have a small team of users who can approve updates to plugins or list new plugins, but we welcome contributions and feedback from everyone! 

We encourage users to review open PRs for new plugins, or updates to existing plugins, and provide feedback on whether the plugins are working as intended. We also welcome reports of listed plugins not working anymore. While we encourage reporters to work with plugin developers, we also accept reports of plugins failing to work properly if the developers are not able to be contacted. 

We occasionally may recruit more people to be valid approvers for new plugins or plugin updates. Generally, we will try and recruit volunteers from established plugin developers. 
