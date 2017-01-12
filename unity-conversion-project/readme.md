# Basic Information

## What is this shit?

This shit is a converter to be used in conjunction with the Virtual Showroom
Asset Backend for Unity. It takes the path to a folder containing textures,
model files and materials and spits out a well-prepared asset bundle.

## Why do we even need this?

We need this to prepare assets so they can be loaded at runtime in any
Virtual Showroom Application.

## How does it work?

At the core of the functionality, we use the magic of the Unity Editor which
already allows us to export well prepared Asset Bundles that can be loaded at
runtime. You can read more about  Asset Bundles
[here](http://docs.unity3d.com/Manual/AssetBundlesIntro.html).

# Usage

## Requirements

1. The path to the Unity Editor executable
(e.g. at `C:\Program Files\Unity\Editor\Unity.exe`)
2. All the assets that need to be converted (and exported as a Unity Asset
Bundle which can then be reimported)

## Steps

1. Copy all the assets you want to export as an Unity Asset Bundle the folder
`Assets\BundleAssets\` of this project.
2. Run the following command to trigger the conversion
(you can read more about the Unity command line
flags and their meaning [here](https://docs.unity3d.com/Manual/CommandLineArguments.html)

```
<path-to-unity-exe> -quit -nographics -batchmode \
-projectPath <path-to-this-project> -executeMethod AutoAssetBundles.AutoBuild \
-logFile <some-path-to-some-logfile>
```

### Notes

* `<path-to-unity-exe>`: Should be the path to the Unity Editor executable as described above
* `<path-to-this-project>`: Should be the absolute or relative path to your local copy of this project
* `<some-path-to-some-logfile>`: You can name your logfile however you like. Also, you can put it wherever you like (granted you specify the path correctly here)

### Example

A complete example of the command could look like this:

```
C:\Program Files\Unity\Editor\Unity.exe -quit -nographics -batchmode \
-projectPath C:\Users\admin\Documents\Projects\fbx-converter-unity \
-executeMethod AutoAssetBundles.AutoBuild -logFile C:\logs\fbx-converter.log
```

You will not get any output from the command. All output is written to the logfile automatically by [Unity](https://docs.unity3d.com/Manual/CommandLineArguments.html).

# Known Issues

There's probably some issues. These may include but are not limited to:

- **Testing**: This piece of shit software isn't thoroughly tested. It works for our requirements but is highly specialized and prune to error.
- **Version Support**: This piece of shit software works with Unity Editor 5.3. Potentially also with higher versions. Probably not with lower ones. We don't give a shit about testing this early.
