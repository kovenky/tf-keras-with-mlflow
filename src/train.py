import numpy as np
import tensorflow as tf
from tensorflow import keras
import mlflow
import mlflow.keras
import mlflow.tensorflow
import click
import utils

np.random.seed(42)
tf.random.set_seed(42)

def create_model():
    model = keras.models.Sequential()
    model.add(keras.layers.Dense(512, activation="relu", input_shape=(28 * 28,)))
    # add output layer
    model.add(keras.layers.Dense(10, activation="softmax"))
    return model

def train(run, model_name, data_path, epochs, batch_size, mlflow_custom_log):
    x_train, y_train, x_test, y_test = utils.get_train_data(data_path)
    model = create_model()

    model.compile(
        optimizer="rmsprop",
        loss="categorical_crossentropy",
        metrics=["accuracy"])
    model.summary()
    model.fit(x_train, y_train, epochs=epochs, batch_size=batch_size, verbose=1)
    print("model.type:",type(model))

    test_loss, test_acc = model.evaluate(x_test, y_test)
    print("test_acc:", test_acc)
    print("test_loss:", test_loss)

    if mlflow_custom_log:
        mlflow.log_param("epochs", epochs)
        mlflow.log_param("batch_size", batch_size)

        mlflow.log_metric("test_acc", test_acc)
        mlflow.log_metric("test_loss", test_loss)

        # Save as TensorFlow SavedModel format (MLflow Keras default)
        mlflow.keras.log_model(model, "keras-model", registered_model_name=model_name)
        
        # write model summary
        summary = []
        model.summary(print_fn=summary.append)
        summary = "\n".join(summary)
        with open("model_summary.txt", "w") as f:
            f.write(summary)
        mlflow.log_artifact("model_summary.txt")

    elif model_name:
        utils.register_model(run, model_name)

    # write model as json file
    with open("model.json", "w") as f:
        f.write(model.to_json())
    mlflow.log_artifact("model.json")    

    predictions = model.predict(x_test)
    print("predictions:", predictions)


@click.command()
@click.option("--experiment-name", help="Experiment name", default=None, type=str)
@click.option("--model-name", help="Registered model name", default=None, type=str)
@click.option("--data-path", help="Data path", default=None, type=str)
@click.option("--epochs", help="Epochs", default=5, type=int)
@click.option("--batch-size", help="Batch size", default=128, type=int)
@click.option("--mlflow-custom-log", help="Explicitly log params, metrics and model with mlflow.log_", default=True, type=bool)
@click.option("--keras-autolog", help="Automatically log params, metrics and model with mlflow.keras.autolog", default=True, type=bool)
@click.option("--tensorflow-autolog", help="Automatically log params, metrics and model with mlflow.tensorflow.autolog", default=False, type=bool)
@click.option("--mlflow-autolog", help="Automatically log params, metrics and model with mlflow.autolog", default=True, type=bool)
def main(experiment_name, model_name, data_path, epochs, batch_size, mlflow_autolog, keras_autolog, tensorflow_autolog, mlflow_custom_log):
    print("Options:")
    for k,v in locals().items():
        print(f"  {k}: {v}")

    model_name = None if not model_name or model_name == "None" else model_name
    
    if not mlflow_autolog and not keras_autolog and not tensorflow_autolog:
        mlflow_custom_log = True

    # Set logging
    if keras_autolog:
        mlflow.keras.autolog()
    if tensorflow_autolog:
        mlflow.tensorflow.autolog()
    if mlflow_autolog:
        mlflow.autolog()

    # Set experiment name
    if experiment_name:
        mlflow.set_experiment(experiment_name)

    # start mlflow experiment
    with mlflow.start_run() as run:
        print("MLflow:")
        print("  run_id:",run.info.run_id)
        print("  experiment_id:",run.info.experiment_id)
        mlflow.set_tag("version.mlflow", mlflow.__version__)
        mlflow.set_tag("version.keras", keras.__version__)
        mlflow.set_tag("version.tensorflow", tf.__version__)
        mlflow.set_tag("mlflow_autolog", mlflow_autolog)
        mlflow.set_tag("tensorflow_autolog", tensorflow_autolog)
        mlflow.set_tag("keras_autolog", keras_autolog)
        mlflow.set_tag("mlflow_custom_log", mlflow_custom_log)
        train(run, model_name, data_path, epochs, batch_size, mlflow_custom_log)
    
    # fetch the auto logged parameters and metrics for ended run
    utils.print_auto_logged_info(mlflow.get_run(run_id=run.info.run_id))


if __name__ == "__main__":
    # run main/app
    utils.display_versions()
    main()
    