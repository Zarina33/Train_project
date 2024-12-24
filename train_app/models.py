from django.db import models

class Train(models.Model):
    train_id = models.PositiveIntegerField(unique=True)
    location = models.CharField(max_length=100)
    direction = models.CharField(max_length=100)
    date = models.DateField()
    time = models.CharField(max_length=200)

    def __str__(self):
        return f"Train {self.train_id} - {self.location} to {self.direction}"

class TrainDetail(models.Model):
    train = models.ForeignKey(Train, on_delete=models.CASCADE, related_name='details')
    serial_number = models.CharField(max_length=100)
    image_link = models.URLField()

    def __str__(self):
        return f"Detail {self.serial_number} for Train {self.train.train_id}"

 
