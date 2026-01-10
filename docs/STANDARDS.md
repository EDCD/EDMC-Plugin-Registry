# EDMC Plugin Browser Standards for Listing

Welcome, plugin developer! We're excited to have you here. In order for your plugin to be listed in the official EDMC plugin browser, your plugin must meet certain standards and expectations. These standards exist to help keep the EDMC environment clean, functional, and easy to use for all of our users. 

When submitting your plugin for listing, you agree to follow these standards on an ongoing basis. Failure to uphold the standards may result in your plugin being delisted from the plugin browser. 

## Versioning
(Note: VERSION constant or dunder requirement will not be enforced until later versions of EDMC support auto update functionality.)

Plugins listed should provide a VERSION constant or `__version__` dunder, in the format of a string compatible with Semantic Versioning. This will be called by EDMC in order to compare the most recent version of a plugin against the current installed version. Version strings should always be in the format of strict Semantic Versioning, such as `Major.Minor.Patch`. For more information about Semantic Versioning, visit [semver.org](https://semver.org/#semantic-versioning-specification-semver). 

## Compatibilty
You are responsible for keeping your plugin compatible with the most recent versions of EDMC. When EDMC adds or removes functionality, you are responsible for keeping your plugin updated in a timely manner. If a plugin is not updated between versions or a significant number of users report that the plugin is not compatible with the most recent versions of EDMC, your plugin will be removed.

As EDMC evolves, plugins may be released that are not compatible with older versions of EDMC. Plugin authors are not required to maintain compatibility with older versions of EDMC outside of patch releases. That is to say, for EDMC 6.1.5, plugins listed are only required to be compatible with (at a minimum) version 6.1.0+.

## Licensing
EDMC is licensed under the GNU GPL v2 or later license. Plugins of EDMC are considered "derivative works" under the GPL licensing terms, and must abide by the terms of these licenses. To be listed, your plugin must also be open source and compatible with the GNU GPL v2 or later license. Examples include GNU GPL v2/3, BSD2/3, LGPL, MIT, or other similar licenses.

## Respect for the Ecosystem
You agree that your plugin will be a good steward of the Elite: Dangerous community's resources. Plugins may not perform actions that break Frontier's EULA, provide malicious content or functionality, or cause a disruption to other community services. For example, scraping community webpages instead of using API calls may cause a plugin listing to be denied. 

Similarly, impersonation or squatting on a valuable namespace will not be allowed. Plugins should be named and use namespaces that generally reflect the purpose of the plugin. Plugins should not be written to "jump to the top" of the directory structure alphabetically (such as "1TheBestPlugin"), add tags that give the impression that the plugin provides more functionality than it actually provides, or in any other way be disruptive or confusing to the EDMC ecosystem.

## Least Privilege 
Plugins may not bundle, package, or include more resources or content than is required for the plugin to perform its functions. As an example, plugins may not include content that scrapes browser history if the plugin has no cause for this access. Similarly, plugins may not bundle extra Python modules that aren't needed for the plugin's purpose. 

Furthermore, plugins shall be written so as not to request more system privileges than required. 

## Coding Standards
Code must generally be written to a high standard. This means that code should be readable, well-documented, and conform to the best practices of the language in use. All code must be manually reviewed prior to a plugin submission being accepted for listing. If our manual reviewers can't understand the code or follow it, we can't list it. 

As an example, plugins that use Python code should be written generally in line with PEP8 standards and the best practices established for EDMC code.
