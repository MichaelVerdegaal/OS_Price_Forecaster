from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split
from tensorflow.keras.layers import Dense
from tensorflow.keras.losses import mean_squared_error
from tensorflow.keras.models import Sequential
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.constraints import NonNeg
from tensorflow.python.keras.regularizers import l2

from config import unpickle_obj, save_model
from source.evaluation import plot_fit_curves

# Split dataset
df = unpickle_obj('dataset_influence-crew_1781_augmented')
dtypes = unpickle_obj('dataset_influence-crew_dtypes')
labels = df.pop('sales.price')

X_train, X_test, y_train, y_test = train_test_split(df, labels, random_state=5, train_size=0.8, shuffle=True)

# Compile model
model = Sequential()
model.add(Dense(200,
                activation='relu',
                kernel_regularizer=l2(0.0001),
                bias_regularizer=l2(0.0001)))
model.add(Dense(1))

model.compile(loss=mean_squared_error, optimizer=Adam(0.00001))

# Train model
hist = model.fit(X_train, y_train,
                 batch_size=32,
                 validation_split=0.1,
                 epochs=1000)

# Evaluate model
plot_fit_curves(hist, remove_first=True)
test_results = model.evaluate(X_test, y_test)
print("Test loss", test_results)
y_pred = model.predict(X_test).flatten()
print("R2 score", r2_score(y_test, y_pred))

# Store model
save_model(model, f"model_influence_crew_{len(df)}")
