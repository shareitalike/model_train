# How to Monitor Your Automated Google Cloud Training

Yes! Because the server is running in Google's cloud infrastructure, **you can completely shut down your Windows computer and go to sleep.** 
The exact instructions below explain how to check if it's done and how to download your results.

---

## 1. How to Know When it is Complete

You don't need to run any commands or watch any logs to know when it's done. Our automated Terraform script is designed to do two very visible things the exact second that training finishes:
1. Upload your finished `.zip` model to your Google Cloud Storage Bucket.
2. Delete the `kaithi-ocr-trainer` Virtual Machine to stop billing.

To check the status, all you ever have to do is look at the Google Cloud website:

*   **Check the Virtual Machine:** Go to your [Compute Engine Dashboard](https://console.cloud.google.com/compute).
    *   If you see the `kaithi-ocr-trainer` VM in the list, it means it is **still training.**
    *   If the `kaithi-ocr-trainer` VM has disappeared from the list, it means training is **finished!**

*   **Check the Storage Bucket:** Go to your [Cloud Storage Dashboard](https://console.cloud.google.com/storage/browser).
    *   Click on your bucket name (e.g., `kaithi-models-av-52431`).
    *   If you look inside and see `my_trained_model.zip`, it means training is **finished!**

---

## 2. How to Download the Resultant Model

Once the training is complete and your VM has successfully deleted itself, you no longer need the command line at all. Do this straight from your web browser:

1. Open your web browser and navigate to the [Google Cloud Storage Browser](https://console.cloud.google.com/storage/browser).
2. Click on the name of your bucket (e.g., `kaithi-models-av-52431`).
3. You will see a file named `my_trained_model.zip`.
4. Click the file name. On the next page, click the **Download** button at the top of the screen to save it to your Windows Desktop.

*(If you don't see the file yet, simply check back later. Just remember that CPU training takes many, many hours).*

---

## 3. Final Cleanup

After you have safely downloaded the `.zip` file to your computer, you have essentially zero billing left because the expensive VM deleted itself. However, Google might still charge you ~3 cents per month to keep the 50MB `.zip` file hosted in the storage bucket. 

If you want to absolutely ensure there are ZERO Google Cloud costs moving forward, open your terminal (whenever you want) and run:
```bash
cd C:\AI_study\kaithi-ocr\terraform
terraform destroy -var="project_id=kaithi-ocr-project" -var="bucket_name=kaithi-models-av-52431"
```
*(Type `yes` when prompted).* This single command will delete your Storage Bucket, your Firewall rule, and perfectly clean your Google Cloud account back to empty.
