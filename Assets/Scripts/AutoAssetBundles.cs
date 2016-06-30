using UnityEngine;
using UnityEditor;
using System.Collections;
using System.Collections.Generic;
using System.IO;

[ExecuteInEditMode]
public class AutoAssetBundles : MonoBehaviour {

    public bool isBuilt = false;

    void Awake()
    {
        //isBuilt = AutoBuild();
    }

    void Start()
    {
        if (!isBuilt)
        {
            isBuilt = true;
            AutoBuild();
        } else
        {
            StartCoroutine(LoadAssetBundle());
        }
    }

    IEnumerator LoadAssetBundle()
    {
        string assetBundlePath = @"Assets/AssetBundles/virtual-showroom-renamed-bundle";
        var bundleLoadRequest = AssetBundle.LoadFromFileAsync(assetBundlePath);
        yield return bundleLoadRequest;

        var myLoadedAssetBundle = bundleLoadRequest.assetBundle;
        if (myLoadedAssetBundle == null)
        {
            Debug.Log("Failed to load AssetBundle!");
            yield break;
        }
        Debug.Log("Successfully loaded AssetBundle!");
        // loop over all contained assets
        string[] assetNames = myLoadedAssetBundle.GetAllAssetNames();
        // find the fbx
        string model = "";
        foreach (string item in assetNames)
        {
            Debug.Log(Path.GetExtension(item));
            if (Path.GetExtension(item) == ".fbx")
            {
                model = item;
                break;
            }
        }
        if (model != "")
        {
            var assetLoadRequest = myLoadedAssetBundle.LoadAssetAsync<GameObject>(model);
            yield return assetLoadRequest;

            GameObject prefab = assetLoadRequest.asset as GameObject;
            Instantiate(prefab);

            myLoadedAssetBundle.Unload(false);
        }
    }

    public static void AutoBuild()
    {
        //format the paths, i know this is ugly as fuck but meh
        List<string> bundleAssets = new List<string>();
        foreach (string file in Directory.GetFiles(Application.dataPath + @"/BundleAssets/"))
        {
            Debug.Log(file);
            bundleAssets.Add(@"Assets/BundleAssets/" + Path.GetFileName(file));
        }
        //assemble
        AssetBundleBuild[] buildMap = new AssetBundleBuild[1];
        buildMap[0].assetBundleName = "virtual-showroom-bundle";
        buildMap[0].assetNames = bundleAssets.ToArray();

        BuildPipeline.BuildAssetBundles("Assets/AssetBundles", buildMap, BuildAssetBundleOptions.None, BuildTarget.Android);
    }
}
