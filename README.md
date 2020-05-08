# neural-entropy-predictor

Setting up instructions:

1. If you configure for the first time and do not have a `venv` folder, create virtual environment. Instruction for Linux systems:

   ```bash
   python3 -m pip install virtualenv
   python3 -m virtualenv -p `which python3` venv
   ```

2. Activate environment:

   ```bash
   source venv/bin/activate
   ```

3. Update the QRS detection submodule:
    
   ```bash
   git submodule update --init --recursive 
   ```

4. Install dependencies:

   ```bash
   pip install -r requirements_prerequisites.txt
   pip install -r requirements_prerequisites.txt
   pip install -r requirements.txt
   pip install -r requirements_dev.txt
   ```

## Usage

### Annotation of the EDF files

It is possible to take EDF files with the IR channel. Then, each action is classified and then the EDF file is
overwritten, with an additional channel 'Classes', where:

* +1 represents pedal action,
* -1 represents feeder action,
* 0 represents no action.

In order to do that the following command should be executed:

```bash
python3 annotate.py
``` 

   
## References

We use the existing implementation of the Pan-Tomkins algorithm in a ECG QRS Detector.
[![DOI](https://zenodo.org/badge/55516257.svg)](https://zenodo.org/badge/latestdoi/55516257)

For the human ECG, we get the detection ratio: 98%.
