# IT5427 Final Submission

This folder contains the final report in Word and PDF formats and the 11-slide defense presentation. The files use the verified local run `public-20261026T084534Z`.

## Run the local dashboard demo

The working project and its local datasets are kept separately at:

`D:\Dai Hoc\Master\2026A\IT5427\Project\apartment-rental-hanoi`

Open PowerShell and run:

```powershell
Set-Location 'D:\Dai Hoc\Master\2026A\IT5427\Project\apartment-rental-hanoi'
$py = 'D:\envs\dev\Scripts\python.exe'
& $py -m streamlit run dashboard.py --server.port 8501
```

Open <http://127.0.0.1:8501/>. Choose the Public-data prototype view for the report results, or open <http://127.0.0.1:8501/?view=public> directly. The demo uses outputs already generated in the working project; it does not need to rerun Spark.

The submission package excludes raw third-party data and local curation ledgers. Keep the working project folder available for the live demo.
